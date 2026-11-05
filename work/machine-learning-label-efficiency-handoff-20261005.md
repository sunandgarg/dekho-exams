# Machine Learning expansion handoff — label efficiency and triage

This pass adds 12 original Machine Learning article pages, bringing the section from 33 to 45 articles. The two new hub modules cover operational classification triage and label-efficient incremental learning. Both applied projects also appear in the Machine Learning project hub. Public bodies contain semantic HTML, one runnable Python example each, complexity and operating costs, Common Mistakes, and deliberate internal links; they contain no external source URLs.

## New pages

Neighbor, probabilistic and cost-sensitive triage:

- `machine-learning/nearest-neighbor-distance-and-local-support`
- `machine-learning/naive-bayes-smoothing-and-dependent-features`
- `machine-learning/fold-local-feature-selection-and-stability`
- `machine-learning/class-weighting-versus-decision-thresholds`
- `machine-learning/multiclass-confusion-and-action-costs`
- `machine-learning/handoff-triage-model-review-project`

Label efficiency and incremental decisions:

- `machine-learning/pseudo-label-selection-and-contamination-control`
- `machine-learning/weak-label-rules-coverage-and-conflicts`
- `machine-learning/active-learning-uncertainty-and-diversity`
- `machine-learning/online-updates-with-delayed-feedback`
- `machine-learning/label-prior-shift-and-odds-adjustment`
- `machine-learning/label-budget-and-incremental-learning-project`

The new bodies contain 7,103 prose-and-code words and 114 internal article links. Existing lessons were cross-linked into each new part of the progression.

## Research checked during this pass

Preferred sites were searched first, followed by primary documentation for technical verification. BeginnersBook and CodingNomads searches did not yield a specific technical detail needed for these topics. The links below are editorial notes only; none appear in public lesson bodies.

- https://www.geeksforgeeks.org/machine-learning/naive-bayes-classifiers/
- https://www.geeksforgeeks.org/machine-learning/k-nearest-neighbours/
- https://www.geeksforgeeks.org/machine-learning/feature-subset-selection-process/
- https://www.geeksforgeeks.org/machine-learning/pseudo-labelling-semi-supervised-learning/
- https://www.geeksforgeeks.org/machine-learning/active-learning-for-reducing-labeling-costs/
- https://www.w3schools.com/Python/python_ml_knn.asp
- https://www.w3schools.com/python/python_ml_confusion_matrix.asp
- https://scikit-learn.org/stable/modules/neighbors.html
- https://scikit-learn.org/stable/modules/naive_bayes.html
- https://scikit-learn.org/stable/modules/linear_model.html
- https://scikit-learn.org/stable/auto_examples/semi_supervised/plot_self_training_varying_threshold.html
- https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.SGDClassifier.html
- https://www.snorkel.org/use-cases/crowdsourcing-tutorial
- https://arxiv.org/abs/1901.06852

## Verification and publication state

- All 12 new Python blocks executed successfully after correcting the weak-label conflict demonstration.
- `python3 scripts/check-ai-data-content.py` passed: 355 AI & Data articles, 45 Machine Learning articles and 3,342 AI & Data internal links.
- `node scripts/check-tutorial-html.mjs` and `git diff --check` passed.
- `npm run build` passed.
- `python3 scripts/export-ai-data-for-wordpress.py` produced 404 draft entries in `work/aitrove-ai-data-import-drafts.json`. No live WordPress publication occurred.

## Remaining distinct coverage

Further standalone topics could examine uncertainty decomposition, model fairness by decision slice, representation learning, causal feature selection, transfer learning, federated constraints, and reinforcement learning. They need separate data and evaluation contracts rather than short additions to these pages. An AI-detection or humanization percentage was not measured.
