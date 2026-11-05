# Machine Learning content pass — incomplete labels and shared tasks

## Delivered

Eleven original pages were added to `src/data/fixtures.json` and the Machine Learning hubs:

- Positive–unlabeled learning: five tutorials on observation state, label-selection mechanisms, prior sensitivity, nonnegative risk arithmetic and independently adjudicated evaluation, plus a release-review project.
- Multi-task learning: four tutorials on target/label contracts, masked per-head losses, loss balance and gradient conflict, and paired negative-transfer review, plus a release-review project.

Generators: `work/add-machine-learning-positive-unlabeled-20261005.py` and `work/add-machine-learning-multitask-20261005.py`. They use `work/ml_fixture_writer_20261005.py`. Crosslinks from existing lessons and hub modules were added. Public article bodies contain no research URLs.

## Verification

- `python3 scripts/check-ai-data-content.py`: passed; 431 AI & Data articles, 121 Machine Learning articles, 4,197 AI & Data internal links.
- `node scripts/check-tutorial-html.mjs`: passed.
- All 11 embedded Python examples compiled and ran with passing assertions.
- New pages contain 386–439 prose words excluding code and 7–11 internal links each.
- `git diff --check`: passed.
- `python3 scripts/export-ai-data-for-wordpress.py`: 480 draft entries; all 11 new paths present as drafts.
- `npm run build`: passed, with the existing large-chunk advisory. Live route rendering was not verified in this pass.

## Editorial research trail (not in public article bodies)

- https://www.geeksforgeeks.org/machine-learning/why-positive-unlabeled-learning/
- https://cseweb.ucsd.edu/~elkan/posonly.pdf
- https://proceedings.neurips.cc/paper_files/paper/2017/hash/7cce53cf90577442771720a370c3c723-Abstract.html
- https://proceedings.mlr.press/v94/bekker18a/bekker18a.pdf
- https://www.geeksforgeeks.org/introduction-to-multi-task-learningmtl-for-deep-learning/
- https://www.tensorflow.org/guide/keras/training_with_built_in_methods
- https://www.tensorflow.org/recommenders/examples/multitask
- https://arxiv.org/abs/2001.06782

## Remaining scope

The Machine Learning curriculum is broad but not exhaustive. Further distinct modules could cover survival prediction as an ML deployment workflow, deeper graph representation learning, structured prediction and self-supervised pretraining. WordPress publishing was not performed; the local export remains drafts.
