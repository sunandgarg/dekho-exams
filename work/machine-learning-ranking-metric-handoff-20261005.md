# Machine Learning content pass — ranking and metric learning

## Delivered

Twelve original pages were added in two complete modules, each with five tutorials and a release-review project.

- Learning to rank: query/label contract, pairwise loss, NDCG at K, click position bias, candidate recall and serving cost, maintenance-search release review.
- Metric learning: similarity/identity contract, triplet geometry, hard-negative mining, embedding retrieval and collapse checks, exact-versus-approximate index audit, visual part-matching release review.

The generators are `work/add-machine-learning-ranking-20261005.py` and `work/add-machine-learning-metric-learning-20261005.py`. They use the idempotent `work/ml_fixture_writer_20261005.py` writer. All pages are in `src/data/fixtures.json`, linked from the Machine Learning tutorial/project hubs and relevant existing lessons. Public article bodies contain no research URLs.

## Verification

- `python3 scripts/check-ai-data-content.py` passed: 409 AI & Data articles, 99 Machine Learning articles, 3,967 internal links to AI & Data.
- `node scripts/check-tutorial-html.mjs` passed.
- All 12 embedded Python snippets compiled and ran with passing assertions.
- New pages contain 401–454 prose words outside code and 6–12 internal links each.
- `git diff --check` passed.
- `python3 scripts/export-ai-data-for-wordpress.py` produced 458 draft entries; all 12 new routes are present with draft status.
- `npm run build` passed. Its existing large-chunk advisory remains. Live route rendering was not verified in this pass.

## Editorial research trail (not in public article bodies)

- https://www.geeksforgeeks.org/machine-learning/catboost-ranking-metrics-a-comprehensive-guide/
- https://www.geeksforgeeks.org/machine-learning/normalized-discounted-cumulative-gain-multilabel-ranking-metrics-ml/
- https://www.geeksforgeeks.org/artificial-intelligence/metric-learning/
- https://xgboost.readthedocs.io/en/release_3.2.0/tutorials/learning_to_rank.html
- https://scikit-learn.org/stable/modules/generated/sklearn.metrics.ndcg_score.html
- https://research.google.com/pubs/archive/45286.pdf
- https://docs.pytorch.org/docs/stable/generated/torch.nn.TripletMarginLoss.html
- https://github.com/facebookresearch/faiss/wiki/guidelines-to-choose-an-index

## Remaining scope

This pass does not make the Machine Learning curriculum exhaustive. Survival prediction, richer graph representation learning, federated evaluation, and causal ML could each support separate modules. The WordPress bundle is a local draft export, not a publication.
