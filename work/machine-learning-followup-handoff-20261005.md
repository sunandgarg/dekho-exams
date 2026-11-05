# Machine Learning follow-up handoff — 2026-10-05

This follow-up adds 12 original Machine Learning article pages in two connected modules, bringing the section from 21 to 33 articles. Public bodies are semantic HTML with one runnable Python block per page, cost analysis, Common Mistakes and deliberate internal links. The new pages contain about 7,500 prose-and-code words and 107 internal links. The site fixture is for local preview; WordPress publishing remains separate.

## Added pages

Ensembles, uncertainty and operations:

- `machine-learning/bootstrap-bagging-and-out-of-bag-evaluation`
- `machine-learning/random-forest-feature-subsampling-and-leaf-support`
- `machine-learning/gradient-boosting-residuals-and-early-stopping`
- `machine-learning/learning-curves-and-training-size-diagnosis`
- `machine-learning/paired-bootstrap-model-gain-intervals`
- `machine-learning/feature-drift-and-delayed-label-monitoring`
- `machine-learning/ensemble-release-review-project`

Classification boundaries and density structure:

- `machine-learning/logistic-regression-log-loss-and-odds`
- `machine-learning/linear-margin-classifiers-and-hinge-loss`
- `machine-learning/dbscan-core-border-and-noise-points`
- `machine-learning/agglomerative-linkage-and-cluster-cuts`
- `machine-learning/classification-and-segmentation-review-project`

Both modules are registered in the Machine Learning hub; both project pages are also registered in the project hub. Existing and new articles cross-link to the added pages. No public body contains external source links or copied source examples.

## Research checked during this pass

Preferred-site material reviewed for coverage, with technical behavior verified against primary documentation:

- https://www.geeksforgeeks.org/machine-learning/what-is-bagging-classifier/
- https://www.geeksforgeeks.org/machine-learning/random-forest-algorithm-in-machine-learning/
- https://www.geeksforgeeks.org/machine-learning/ml-gradient-boosting/
- https://www.geeksforgeeks.org/machine-learning/understanding-logistic-regression/
- https://www.geeksforgeeks.org/machine-learning/support-vector-machine-algorithm/
- https://www.geeksforgeeks.org/machine-learning/dbscan-clustering-in-ml-density-based-clustering/
- https://www.w3schools.com/python/python_ml_logistic_regression.asp
- https://www.w3schools.com/python/python_ml_hierarchial_clustering.asp
- https://scikit-learn.org/stable/modules/ensemble.html
- https://scikit-learn.org/stable/modules/learning_curve.html
- https://scikit-learn.org/stable/modules/linear_model.html
- https://scikit-learn.org/stable/modules/svm.html
- https://scikit-learn.org/stable/modules/generated/sklearn.cluster.AgglomerativeClustering.html
- https://developers.google.com/machine-learning/crash-course/production-ml-systems/monitoring

The two other requested beginner-oriented sites were checked through topic searches, but did not contribute a reliable technical detail needed for these new subjects. Research links stay in this internal handoff only.

## Verification

- All 12 new Python examples executed successfully.
- `python3 scripts/check-ai-data-content.py` passed: 343 AI & Data articles, 33 Machine Learning articles and 3,204 AI & Data internal links.
- `node scripts/check-tutorial-html.mjs`, `git diff --check` and `npm run build` passed.
- `python3 scripts/export-ai-data-for-wordpress.py` produced 392 entries, all drafts, in `work/aitrove-ai-data-import-drafts.json`.

## Still distinct future topics

Nearest-neighbor models, naive Bayes, feature selection, class weighting, multiclass policy, semi-supervised learning, weak supervision, active learning and online learning remain plausible separate pages. They should be added as full lessons with validated examples and links, not as filler sections. No live publication or humanization-score test occurred in this pass.
