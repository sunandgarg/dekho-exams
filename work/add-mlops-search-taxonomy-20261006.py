"""Publish search governance and label-taxonomy migration modules."""
from de_batch_publisher import publish

M = 'mlops/'
S = 'Distributed experiment search governance'
T = 'Label taxonomy migrations and dual evaluation'

lessons = [
    {
        'path': M + 'search-trial-lineage-and-resource-isolation',
        'title': 'Distributed model search: trial lineage and resource isolation',
        'module': S, 'project': False,
        'summary': 'A search result is useful only when each trial has a comparable dataset, split, metric and resource budget.',
        'sections': [
            ('Freeze the search contract', 'A parcel-damage model search runs many candidates in parallel. Pin the training snapshot, feature code, split IDs, target definition, metric implementation and search-space revision before dispatch. Each trial receives a unique ID, parameter set, seed policy, image digest and resource request. A trial that reads a newer dataset is a separate experiment, even if its parameters look identical. [[mlops/run-manifest-and-artifact-lineage|Run manifests]] provide the artifact trail; [[mlops/snapshot-split-and-environment-replay|snapshot replay]] keeps the comparison fair.'),
            ('Separate workers and side effects', 'Trial workers should write outputs under unique IDs and never share a mutable checkpoint path. An interrupted worker may retry the same trial ID only under an idempotent claim, or it may create duplicate results that skew selection. Limit CPU, accelerator, memory and concurrent trials so the search cannot starve serving or other training jobs. Record queued, running, pruned, failed and completed states. [[mlops/training-budget-and-resource-admission|Training admission]] supplies the larger resource boundary.'),
            ('Keep selection data out of training', 'Fit preprocessing within each training fold and evaluate on its corresponding validation fold. Do not inspect the untouched final set after every trial or adapt the search space to it; repeated peeking turns it into a tuning set. Group or time boundaries must match deployment. A high validation score from leaked entity overlap is not a production gain. [[mlops/feature-training-serving-parity|Feature parity]] and [[mlops/slice-quality-gates-and-uncertainty|slice gates]] test the selected candidate after the search.'),
            ('Promote the reproducible winner', 'Store the winner’s full trial lineage and rerun it from the pinned snapshot. Compare the rerun within a stated tolerance, then evaluate it once on the reserved final set and against the approved baseline. Report failed and pruned trials rather than only the winner. [[mlops/pruning-budgets-and-fair-trial-comparison|Pruning controls]] define fair early stops; [[mlops/parcel-model-search-project|the project]] catches two workers that accidentally share a checkpoint prefix.'),
        ],
        'code': '''def trial_identity(trial, search_manifest):
    required = ("snapshot_digest", "split_digest", "metric_revision",
                "search_revision")
    for name in required:
        if trial.get(name) != search_manifest.get(name):
            return "reject:" + name
    if not trial.get("trial_id") or not trial.get("image_digest"):
        return "reject:identity"
    return "admit"

manifest = {"snapshot_digest": "parcel-s47", "split_digest": "group-r8",
            "metric_revision": "miss-cost-r3", "search_revision": "space-r4"}
trial = {**manifest, "trial_id": "parcel-trial-82", "image_digest": "image-r31"}
assert trial_identity(trial, manifest) == "admit"
assert trial_identity({**trial, "split_digest": "random-r7"},
                      manifest) == "reject:split_digest"
''',
        'cost': 'The identity check is O(k) time and O(1) extra space for k pinned fields. The search itself costs the sum of trial training time and storage, plus scheduler contention. Strong resource isolation may leave some accelerators temporarily idle but prevents a broad search from delaying approved production work.',
        'mistakes': ['Comparing trials trained on different snapshots under one search ID.', 'Letting workers overwrite a shared checkpoint path.', 'Tuning against the final test set after each promising result.', 'Publishing only the best score while hiding trial failures and budget.'],
        'related': [M + 'pruning-budgets-and-fair-trial-comparison', M + 'parcel-model-search-project', M + 'run-manifest-and-artifact-lineage', M + 'snapshot-split-and-environment-replay', M + 'training-budget-and-resource-admission'],
    },
    {
        'path': M + 'pruning-budgets-and-fair-trial-comparison',
        'title': 'Trial pruning: spend less compute without biasing model selection',
        'module': S, 'project': False,
        'summary': 'Early stopping saves resources only when comparable trials report the same metric at the same resource milestones.',
        'sections': [
            ('Define comparable milestones', 'A search scheduler may stop a parcel classifier after a few training epochs if it appears weak. Compare trials after the same examples, epochs or compute budget, not whichever metric arrived first. Record validation split, metric revision and milestone with every report. A worker that processes fewer rows before reporting looks artificially fast. Define how missing metrics and crashes are represented; neither is a zero score. [[mlops/search-trial-lineage-and-resource-isolation|Trial lineage]] keeps the comparison on one frozen problem.'),
            ('Avoid pruning slow starters blindly', 'Some configurations improve late. A strict early cutoff can favor models that learn quickly but plateau below slower candidates. Use a warm-up period and a minimum comparison pool, then inspect how often eventual strong candidates would have been pruned in retrospective experiments. Pruning changes the population from which the winner is chosen; report both the saved compute and the selection risk. [[mlops/training-checkpoints-and-preemption-recovery|Checkpoint recovery]] helps distinguish a slow trial from one repeatedly preempted.'),
            ('Cap the whole search', 'Set a maximum number of trials, total accelerator-hours, wall time and parallel workers before the first result appears. A high metric is not a reason to keep an unbounded search alive. When the cap arrives, stop new trials, retain completed evidence and decide whether more search is justified. Do not silently raise the cap after seeing the final holdout. [[mlops/training-budget-and-resource-admission|Resource admission]] protects the wider fleet while the search is active.'),
            ('Evaluate the winner independently', 'The best validation score among many trials is selection-biased. Rerun the chosen configuration, inspect slices, then measure once on an untouched final set. A deployment decision also needs latency, memory and threshold behavior, not merely the search objective. [[mlops/optimized-model-hardware-matrix-and-fallback|Hardware qualification]] tests the serving path. [[mlops/parcel-model-search-project|The project]] rejects a pruned trial whose metric arrived at an incomparable step and holds a winner with weak rare-damage performance.'),
        ],
        'code': '''def prune_trial(report, reference, minimum_step, allowed_gap):
    if report["metric_revision"] != reference["metric_revision"]:
        return "hold:metric-mismatch"
    if report["step"] != reference["step"]:
        return "hold:step-mismatch"
    if report["step"] < minimum_step:
        return "continue:warmup"
    if report["score"] + allowed_gap < reference["score"]:
        return "prune"
    return "continue"

reference = {"metric_revision": "miss-cost-r3", "step": 82, "score": 0.74}
candidate = {"metric_revision": "miss-cost-r3", "step": 82, "score": 0.61}
assert prune_trial(candidate, reference, 47, 0.08) == "prune"
assert prune_trial({**candidate, "step": 39}, reference, 47, 0.08) == \
       "hold:step-mismatch"
''',
        'cost': 'The pruning decision is O(1) time and space after synchronized reports. Earlier stops can save many trial-hours, but every extra validation report consumes compute and data reads. A fixed gap is only a policy illustration; production thresholds need retrospective analysis of saved cost and discarded eventual winners.',
        'mistakes': ['Comparing trial metrics at different training steps.', 'Recording a crashed trial as a low-performing completed trial.', 'Raising the search budget after viewing final-test results.', 'Treating the best search score as an unbiased estimate of future performance.'],
        'related': [M + 'search-trial-lineage-and-resource-isolation', M + 'parcel-model-search-project', M + 'training-checkpoints-and-preemption-recovery', M + 'training-budget-and-resource-admission', M + 'optimized-model-hardware-matrix-and-fallback'],
    },
    {
        'path': M + 'parcel-model-search-project',
        'title': 'Project: govern a distributed parcel-damage model search',
        'module': S, 'project': True,
        'summary': 'Run a bounded search, reject incomparable trials and evaluate the winner without leaking the final holdout.',
        'sections': [
            ('Freeze the parcel problem', 'The task predicts whether a parcel image needs manual damage review. Group images by shipment so frames from one parcel never appear in both training and validation. Pin the snapshot, group split, feature preprocessing, miss-cost metric, search space and worker image. Set a budget of 82 trials and a finite accelerator-hour cap before dispatch. [[mlops/search-trial-lineage-and-resource-isolation|Trial identity]] rejects workers pointed at a newer image archive or a random split.'),
            ('Exercise worker failure', 'Launch workers with unique trial and checkpoint prefixes. Two accidentally share a prefix; the second resumes a first trial’s checkpoint and emits a plausible metric. Detect the mismatch through trial ID and checkpoint metadata, quarantine both outputs and rerun them cleanly. Another worker reports at step 39 while peers report at step 82; it cannot be pruned by direct score comparison. [[mlops/pruning-budgets-and-fair-trial-comparison|Comparable milestones]] define the stop rule.'),
            ('Select once, then evaluate', 'At the budget cap, freeze the completed trial list and rerun the chosen configuration from the pinned snapshot. Inspect damage types, camera classes and shipment groups. The top validation candidate improves the global miss-cost objective but loses on crushed-corner parcels; hold it pending a documented quality decision rather than using the untouched final set to pick a different trial. After selection is fixed, evaluate once on the protected final set and record the result without further search.'),
            ('Deliver the release packet', 'Publish trial counts by completed, pruned, failed and quarantined states; total compute, winner lineage, rerun tolerance, slice report and serving-resource estimate. A later search needs a new search revision and its own final evaluation plan. [[mlops/model-registry-promotion-gates|Registry gates]] should receive the selected artifact only after data, performance and slice checks pass. The project is not complete merely because a scheduler returned a best-trial number.'),
        ],
        'code': '''def parcel_search_disposition(trials, budget, selected_trial):
    if budget <= 0 or len(trials) > budget:
        return "hold:budget"
    valid = [trial for trial in trials if trial["state"] == "completed"
             and trial["lineage_ok"]]
    selected = next((trial for trial in valid
                     if trial["trial_id"] == selected_trial), None)
    if selected is None:
        return "hold:invalid-winner"
    if not selected["slice_gate_passed"]:
        return "hold:slice-quality"
    return "evaluate:final-holdout"

trials = [{"trial_id": "parcel-47", "state": "completed",
           "lineage_ok": True, "slice_gate_passed": False},
          {"trial_id": "parcel-82", "state": "completed",
           "lineage_ok": True, "slice_gate_passed": True}]
assert parcel_search_disposition(trials, 82, "parcel-47") == "hold:slice-quality"
assert parcel_search_disposition(trials, 82, "parcel-82") == \
       "evaluate:final-holdout"
''',
        'cost': 'The gate is O(t) time and O(t) temporary space for t trial records. Training dominates cost; the fixed budget makes it visible before results tempt expansion. Retrying corrupted trials adds compute, but accepting mixed checkpoints would make the comparison invalid and could waste a later production rollout.',
        'mistakes': ['Sharing checkpoint paths between concurrent trials.', 'Pruning a trial from a metric reported at an earlier step.', 'Using the final holdout to select among the top search trials.', 'Ignoring rare-damage failures because the global objective improved.'],
        'related': [M + 'search-trial-lineage-and-resource-isolation', M + 'pruning-budgets-and-fair-trial-comparison', M + 'model-registry-promotion-gates', M + 'slice-quality-gates-and-uncertainty', M + 'snapshot-split-and-environment-replay'],
    },
    {
        'path': M + 'label-taxonomy-version-and-migration',
        'title': 'Label taxonomy migrations: preserve meaning across retraining',
        'module': T, 'project': False,
        'summary': 'Changing the names or boundaries of target classes changes the learning problem and its evaluation contract.',
        'sections': [
            ('Version meaning, not just spelling', 'A scanner defect classifier originally labels “damaged” or “clear.” The team now needs “torn label,” “blurred print” and “other damage.” This is not a cosmetic rename: an old positive example may fit several new classes and cannot always be mapped without reinspection. Create a taxonomy revision with definitions, examples, exclusion rules and effective date. Pin the revision to every annotation batch, training snapshot, model output and consumer contract. [[mlops/label-corrections-and-evaluation-ledger|Label corrections]] modify judgments within a taxonomy; migration changes the taxonomy itself.'),
            ('Build a mapping with an unknown state', 'Define which old labels map deterministically and which require adjudication. Preserve raw original labels and provenance, then write migrated labels as new records linked to the originals. Do not fill ambiguous cases by guessing from the old class or from model predictions. Track mapping coverage and unresolved counts by source and cohort. [[mlops/training-source-admission-and-quarantine|Source admission]] can hold batches whose taxonomy is missing or inconsistent.'),
            ('Plan consumers and score outputs', 'The new model may emit three damage classes while older clients expect one Boolean. Decide whether a temporary compatibility projection is valid; “any damage” may be safe for manual review but loses the distinction a downstream repair workflow needs. Version the output schema and reject clients that interpret the new class index as the old Boolean. [[mlops/inference-client-migration-and-contract-tests|Client contract tests]] exercise the mixed-version period.'),
            ('Rebuild evaluation evidence', 'Historical quality measured against the binary target cannot be directly compared to three-class quality. Maintain an old-label evaluation view for compatibility, create adjudicated examples for new classes and report both with separate denominators. Stage the migration by consumer readiness and outcome maturity. [[mlops/dual-label-evaluation-and-compatibility|Dual evaluation]] protects the transition; [[mlops/scanner-label-taxonomy-migration-project|the project]] catches an ambiguous legacy class that would otherwise be auto-mapped.'),
        ],
        'code': '''def migrate_defect_label(old_label, mapping):
    if old_label not in mapping:
        return {"state": "hold:unknown-old-label", "new_label": None}
    proposed = mapping[old_label]
    if proposed is None:
        return {"state": "review:ambiguous", "new_label": None}
    return {"state": "mapped", "new_label": proposed}

mapping = {"clear": "clear", "damaged": None,
           "unreadable": "blurred-print"}
assert migrate_defect_label("clear", mapping)["new_label"] == "clear"
assert migrate_defect_label("damaged", mapping)["state"] == "review:ambiguous"
assert migrate_defect_label("torn", mapping)["state"] == "hold:unknown-old-label"
''',
        'cost': 'The mapping lookup is O(1) expected time and space per label. Adjudication cost scales with ambiguous legacy records; storing both revisions increases dataset and lineage storage. Automatic mapping is cheap but incorrect for split classes, so budget human review where old information cannot distinguish the new targets.',
        'mistakes': ['Treating a class split as a string rename.', 'Overwriting historical labels without preserving their taxonomy revision.', 'Guessing a new subclass from an ambiguous old positive label.', 'Sending new class indices to an old Boolean consumer.'],
        'related': [M + 'dual-label-evaluation-and-compatibility', M + 'scanner-label-taxonomy-migration-project', M + 'label-corrections-and-evaluation-ledger', M + 'training-source-admission-and-quarantine', M + 'inference-client-migration-and-contract-tests'],
    },
    {
        'path': M + 'dual-label-evaluation-and-compatibility',
        'title': 'Dual-label evaluation: compare models across a target migration',
        'module': T, 'project': False,
        'summary': 'During a target change, evaluate both the new task and the legacy consumer view without pretending their metrics are identical.',
        'sections': [
            ('Keep two clearly named views', 'The new scanner model emits torn label, blurred print, other damage and clear. The old consumer still needs a binary damaged-versus-clear route. Produce the new four-class output and a reviewed projection to the legacy route. Evaluate native class performance on adjudicated new-taxonomy examples, and evaluate the binary projection on a separate legacy-compatible frame. Do not compare four-class accuracy with old binary accuracy as a before-and-after improvement. [[mlops/label-taxonomy-version-and-migration|Taxonomy revisions]] define both meanings.'),
            ('Measure migration coverage', 'Count records with deterministic mapping, independently relabeled records, unresolved ambiguous records and excluded data. Report quality per new class and by acquisition channel; a strong average can conceal that rare torn labels are missed. When audit labels are selected through review routing, the observed set may be biased. [[mlops/selective-label-observation-and-audit-sampling|Independent audit coverage]] helps estimate errors outside the reviewed queue.'),
            ('Test old clients explicitly', 'Run output contract tests for clients that receive only the projected binary result, and new clients that need the fine-grained class and evidence. Unknown labels, low confidence and malformed outputs must take documented fallbacks. Pin client, model, taxonomy and projection revisions in each decision. [[mlops/inference-request-response-contracts|Response contracts]] prevent a silent shift in field meaning, while [[mlops/inference-client-migration-and-contract-tests|client migration tests]] cover mixed deployments.'),
            ('Cut over only with two passing gates', 'Require acceptable new-class quality and stable legacy route behavior before expanding. The new model can improve fine-grained reporting yet still change the binary review route for older consumers; that is a release failure until examined. Keep the prior model and projection available through the cutover, then retire them only after consumer inventory confirms nobody needs them. [[mlops/model-consumer-inventory-and-retirement-gates|Retirement gates]] close the migration safely; [[mlops/scanner-label-taxonomy-migration-project|the project]] runs the full dual view.'),
        ],
        'code': '''def legacy_damage_route(new_label, projection):
    if new_label not in projection:
        return "manual-review:unknown-label"
    return "review" if projection[new_label] else "release"

projection = {"clear": False, "torn-label": True,
              "blurred-print": True, "other-damage": True}
assert legacy_damage_route("torn-label", projection) == "review"
assert legacy_damage_route("clear", projection) == "release"
assert legacy_damage_route("possible-tear", projection) == \
       "manual-review:unknown-label"
''',
        'cost': 'Projection lookup is O(1) expected time and space. Dual evaluation runs two metric suites and may require extra adjudication and storage for newly labeled records. The cost is temporary but necessary: a single aggregate score cannot establish both new-task quality and compatibility with the old decision route.',
        'mistakes': ['Comparing old binary accuracy directly with new four-class accuracy.', 'Using ambiguous mapped records as if they were adjudicated labels.', 'Testing the new model without exercising older clients.', 'Retiring the binary projection before consumer inventory reaches zero.'],
        'related': [M + 'label-taxonomy-version-and-migration', M + 'scanner-label-taxonomy-migration-project', M + 'selective-label-observation-and-audit-sampling', M + 'inference-client-migration-and-contract-tests', M + 'model-consumer-inventory-and-retirement-gates'],
    },
    {
        'path': M + 'scanner-label-taxonomy-migration-project',
        'title': 'Project: split scanner defect labels without breaking old clients',
        'module': T, 'project': True,
        'summary': 'Migrate a binary defect label into specific classes, review ambiguous history and stage a dual-output model.',
        'sections': [
            ('Freeze old and new definitions', 'A scanner fleet currently marks shipping labels damaged or clear. Operations now distinguishes torn labels, blurred print and other damage because each routes to a different repair action. Publish exact class definitions and a new taxonomy revision. Preserve original labels and annotation source IDs. The old damaged class cannot be split from its name alone, so create an adjudication queue rather than an automatic remap. [[mlops/label-taxonomy-version-and-migration|Migration rules]] keep unknown records explicit.'),
            ('Build a clean transition snapshot', 'Take a pinned training snapshot, deterministically map clear and any independently verified unreadable cases, then relabel a sampled set of old damaged cases from retained source evidence. Exclude or hold records whose evidence is unavailable. Split by shipment and time, fitting preprocessing only inside training folds. Keep the new evaluation set independent of records used to settle migration choices. [[mlops/snapshot-split-and-environment-replay|Snapshot replay]] lets an editor reconstruct both views.'),
            ('Test both client generations', 'Train a four-class candidate and define a reviewed projection to old binary routes. Run native class quality, rare torn-label slices, confidence failures and the old route contract on frozen examples. A new label code that an old client interprets as clear must fail contract tests. Stage new and old clients separately, logging model digest, taxonomy revision and projection revision. [[mlops/dual-label-evaluation-and-compatibility|Dual evaluation]] prevents a better four-class score from hiding a worse binary route.'),
            ('Finish with a reversible cutover', 'Promote only after both quality and compatibility gates pass. Keep the prior model and binary projection until the consumer inventory shows all clients upgraded. Record remaining ambiguous history and exclude it from claims about new-class quality. If a new client fails, restore the prior complete route while preserving labels and lineage; do not rewrite historical examples to fit the rollback. [[mlops/model-consumer-inventory-and-retirement-gates|Retirement checks]] determine when old output support can actually end.'),
        ],
        'code': '''def taxonomy_cutover_gate(class_gate, legacy_gate,
                          unresolved_records, allowed_unresolved):
    if unresolved_records < 0 or allowed_unresolved < 0:
        raise ValueError("invalid unresolved count")
    if not class_gate:
        return "hold:new-classes"
    if not legacy_gate:
        return "hold:legacy-route"
    if unresolved_records > allowed_unresolved:
        return "hold:adjudication"
    return "stage:dual-output"

assert taxonomy_cutover_gate(True, True, 39, 47) == "stage:dual-output"
assert taxonomy_cutover_gate(True, False, 39, 47) == "hold:legacy-route"
assert taxonomy_cutover_gate(True, True, 82, 47) == "hold:adjudication"
''',
        'cost': 'The gate is O(1) time and space after evaluation. Relabeling ambiguous history and running two client contracts cost time, but prevent an apparently successful new classifier from breaking old routing. Maintaining dual output temporarily adds code and monitoring; retire it only when actual consumer usage and contract evidence support removal.',
        'mistakes': ['Auto-splitting the old damaged class without image evidence.', 'Combining old and new taxonomies under one accuracy figure.', 'Deploying new class indices to older clients.', 'Deleting the compatibility route before all consumers migrate.'],
        'related': [M + 'label-taxonomy-version-and-migration', M + 'dual-label-evaluation-and-compatibility', M + 'snapshot-split-and-environment-replay', M + 'inference-client-migration-and-contract-tests', M + 'model-consumer-inventory-and-retirement-gates'],
    },
]

crosslinks = [
    (M + 'run-manifest-and-artifact-lineage', M + 'search-trial-lineage-and-resource-isolation'),
    (M + 'training-budget-and-resource-admission', M + 'pruning-budgets-and-fair-trial-comparison'),
    (M + 'snapshot-split-and-environment-replay', M + 'parcel-model-search-project'),
    (M + 'label-corrections-and-evaluation-ledger', M + 'label-taxonomy-version-and-migration'),
    (M + 'inference-client-migration-and-contract-tests', M + 'dual-label-evaluation-and-compatibility'),
    (M + 'model-consumer-inventory-and-retirement-gates', M + 'scanner-label-taxonomy-migration-project'),
]

if __name__ == '__main__':
    publish(lessons, (S, T), crosslinks,
            'aitrove-mlops-search-taxonomy-import-20261006.json', 6202,
            subject='mlops', hub_path=M + 'mlops-tutorial')
