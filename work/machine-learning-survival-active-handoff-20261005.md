# Machine Learning content pass — time-to-event models and active learning

## Delivered

Eleven original pages were added to `src/data/fixtures.json` and the Machine Learning tutorial and project hubs:

- Operational survival modeling: five tutorials on event/censor contracts, risk sets and landmarks, time-varying features, supported-horizon evaluation, and competing events/service policy, plus a fleet battery-timing release project.
- Active learning: four tutorials on eligible pool snapshots, budgeted batch selection, annotator disagreement, and independent evaluation/stopping, plus an invoice-label acquisition release project.

Generators: `work/add-machine-learning-survival-20261005.py` and `work/add-machine-learning-active-learning-20261005.py`, using `work/ml_fixture_writer_20261005.py`. The pages crosslink to existing Machine Learning and Data Science material; nine existing pages received inward links. Public article bodies have no external links.

## Verification

- `python3 scripts/check-ai-data-content.py`: passed; 453 AI & Data articles, 143 Machine Learning articles, 4,395 AI & Data internal links.
- `node scripts/check-tutorial-html.mjs`: passed.
- All 11 embedded Python examples compiled and ran with passing assertions.
- The 11 new pages have about 419–489 text words each, including headings and link labels, and 6–11 internal body links each.
- Banned editorial terms and external links: none in these pages.
- `git diff --check`: passed.
- `python3 scripts/export-ai-data-for-wordpress.py`: 502 draft entries; all 11 new paths present as drafts.
- `npm run build`: passed with the pre-existing client chunk-size advisory.

## Editorial research trail (not in public article bodies)

- https://www.geeksforgeeks.org/data-science/cox-proportional-hazards-model/
- https://www.geeksforgeeks.org/data-analysis/censoring-and-truncation/
- https://stat.ethz.ch/R-manual/R-devel/library/survival/doc/timedep.pdf
- https://stat.ethz.ch/R-manual/R-devel/library/survival/html/timeline.html
- https://scikit-survival.readthedocs.io/en/v0.25.0/user_guide/evaluating-survival-models.html
- https://www.geeksforgeeks.org/machine-learning/active-learning-for-reducing-labeling-costs/
- https://minds.wisconsin.edu/handle/1793/60660
- https://ojs.aaai.org/index.php/AAAI/article/view/5640
- https://aclanthology.org/P08-2017/
- https://proceedings.mlr.press/v139/kossen21a/kossen21a.pdf

## Remaining scope

The Machine Learning section is not exhaustive. Distinct future modules could cover online adaptation under delayed labels, sequence-to-sequence generation evaluation, deeper graph representation release workflows, and acquisition under changing class taxonomies. Live browser rendering was not verified in this pass. The export is a draft artifact; no WordPress publication occurred. No humanization detector score was measured.
