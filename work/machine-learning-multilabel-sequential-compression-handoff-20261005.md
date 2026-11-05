# Machine Learning content pass — 2026-10-05

## Delivered

Added 18 original Machine Learning fixture articles: five tutorials and one project in each of three new modules.

- Multi-label classification: unknown targets, binary relevance and label dependence, per-label thresholds, metrics, calibration, release review.
- Sequential decisions: state/reward contract, Bellman iteration, temporal difference returns, Q-learning, offline-support limits, policy review.
- Model compression: device budgets, distillation, structured pruning, affine quantization, Pareto/shadow checks, release review.

The source generators are `work/add-machine-learning-multilabel-20261005.py`, `work/add-machine-learning-sequential-20261005.py`, and `work/add-machine-learning-compression-20261005.py`. The shared writer is `work/ml_fixture_writer_20261005.py`. The material is in `src/data/fixtures.json`, linked from the Machine Learning tutorial and project hubs, and crosslinked with relevant existing lessons.

## Verification

- `python3 scripts/check-ai-data-content.py`: passed; 397 AI & Data articles, 87 Machine Learning articles, 3,842 AI & Data internal links.
- `node scripts/check-tutorial-html.mjs`: passed.
- All 18 embedded Python snippets compiled and ran, including assertions.
- Each new page has 8–13 internal links and 383–452 prose words excluding the code block.
- `python3 scripts/export-ai-data-for-wordpress.py`: 446 entries in `work/aitrove-ai-data-import-drafts.json`; all 18 new entries included with `draft` status.
- `git diff --check`: passed.
- `npm run build`: passed, with the existing large-chunk advisory. No live route test was run in this pass.

## Editorial research trail (not in public article bodies)

- https://www.geeksforgeeks.org/machine-learning/an-introduction-to-multilabel-classification/
- https://www.geeksforgeeks.org/machine-learning/bellman-equation/
- https://www.geeksforgeeks.org/machine-learning/markov-decision-process/
- https://www.geeksforgeeks.org/machine-learning/knowledge-distillation/
- https://scikit-learn.org/stable/modules/generated/sklearn.metrics.hamming_loss.html
- https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html
- https://scikit-learn.org/stable/auto_examples/multioutput/plot_classifier_chain_yeast.html
- https://spinningup.openai.com/en/latest/spinningup/rl_intro.html
- https://inst.eecs.berkeley.edu/~cs188/textbook/mdp/value-iteration.html
- https://inst.eecs.berkeley.edu/~cs188/textbook/rl/mfl.html
- https://www.tensorflow.org/model_optimization/guide
- https://docs.pytorch.org/tutorials/beginner/knowledge_distillation_tutorial.html

## Remaining scope

The Machine Learning curriculum is extensive but not exhaustive. Distinct future modules could cover survival prediction, graph learning at more depth, federated evaluation, causal ML, and privacy-preserving training. They were not added in this pass. The export is local draft data; WordPress publishing was not performed.
