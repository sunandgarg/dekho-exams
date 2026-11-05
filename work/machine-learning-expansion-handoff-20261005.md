# Machine Learning expansion handoff — 2026-10-05

The local AI Trove fixture now contains 21 Machine Learning article pages, up from nine. This pass added 12 new pages in two connected modules. It also added links from existing lessons, registered each new tutorial in the Machine Learning hub, and registered both projects in the project hub. These fixture rows support local preview; the WordPress export is a draft file and is not live publication.

## New pages

Core models and operating metrics:

- `machine-learning/regression-baselines-and-holdout-metrics`
- `machine-learning/regression-error-slices-and-tail-cost`
- `machine-learning/ridge-regularization-with-training-only-scaling`
- `machine-learning/rare-event-precision-recall-and-prevalence`
- `machine-learning/decision-tree-splits-and-leaf-support`
- `machine-learning/shipment-delay-model-review-project`

Selection, inspection and unsupervised structure:

- `machine-learning/hyperparameter-search-and-untouched-test`
- `machine-learning/permutation-importance-on-held-out-data`
- `machine-learning/distance-scaling-before-clustering`
- `machine-learning/k-means-objective-and-restart-stability`
- `machine-learning/principal-components-and-variance-retention`
- `machine-learning/segmentation-and-model-selection-project`

Each body contains an original operational example, a runnable Python block, performance and operating cost, common mistakes, and internal links. The 12 pages contain approximately 7,200 prose-and-code words in total. Public article bodies contain no external references or URLs.

## Verification

- All 12 Python examples executed successfully.
- `python3 scripts/check-ai-data-content.py` passed: 331 AI & Data articles, 21 Machine Learning articles, 3,072 AI & Data internal links.
- `node scripts/check-tutorial-html.mjs` passed.
- `git diff --check` passed.
- `npm run build` passed.
- `python3 scripts/export-ai-data-for-wordpress.py` produced 380 draft entries in `work/aitrove-ai-data-import-drafts.json`.

## Next coverage gaps

Separate future pages could cover bagging and random forests, boosting, margin classifiers, bootstrap uncertainty, learning curves, drift diagnosis and retraining policy. They should follow the same boundary-first examples and be linked into the existing Machine Learning progression. The current pass does not claim to exhaust the field or certify an AI-detection score.
