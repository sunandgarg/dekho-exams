# Machine Learning content pass — federated training and explanations

## Delivered

Added eleven original pages in two new modules to `src/data/fixtures.json` and the Machine Learning hubs.

- Federated training and site-level evaluation: five tutorials on client contracts, weighted aggregation, non-IID updates, participation/dropout and site denominators, plus a depot release-review project.
- Model explanations and action limits: four tutorials on correlated feature perturbations, PDP/ICE support, feasible model edits and fidelity/stability, plus a pump-risk explanation release-review project.

The idempotent generators are `work/add-machine-learning-federated-20261005.py` and `work/add-machine-learning-explanations-20261005.py`; both use `work/ml_fixture_writer_20261005.py`. Relevant existing lessons link back into the new modules. The public article bodies contain no research URLs.

## Verification

- `python3 scripts/check-ai-data-content.py`: passed; 420 AI & Data articles, 110 Machine Learning articles, 4,085 AI & Data internal links.
- `node scripts/check-tutorial-html.mjs`: passed.
- All 11 embedded Python snippets compiled and ran with passing assertions.
- Each new page contains 384–451 prose words excluding code and 7–13 internal links.
- `git diff --check`: passed.
- `python3 scripts/export-ai-data-for-wordpress.py`: 469 draft entries; all 11 new routes present as drafts.
- `npm run build`: passed, with the existing large-chunk advisory. Live route rendering was not verified in this pass.

## Editorial research trail (not in public article bodies)

- https://research.google/pubs/communication-efficient-learning-of-deep-networks-from-decentralized-data/
- https://www.tensorflow.org/federated/tutorials/federated_learning_for_image_classification
- https://flower.ai/docs/framework/main/en/ref-api/flwr.server.strategy.FedAvg.html
- https://www.geeksforgeeks.org/machine-learning/machine-learning-explainability-using-permutation-importance/
- https://scikit-learn.org/stable/auto_examples/inspection/plot_permutation_importance_multicollinear.html
- https://scikit-learn.org/1.2/modules/partial_dependence.html
- https://arxiv.org/abs/1909.09369

## Remaining scope

The curriculum is not exhaustive. Distinct future modules could cover survival prediction in an ML workflow, richer graph representation learning, multi-task models and uncertainty under missing labels. The export is local draft data, not publication to WordPress.
