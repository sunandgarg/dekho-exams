# Machine Learning content pass — unlabeled representations and structured outputs

## Delivered

Eleven original pages were added to `src/data/fixtures.json` and both Machine Learning hubs:

- Self-supervised learning: five tutorials on valid views, masked reconstruction, contrastive pair collisions, frozen representation probes, and corpus provenance, plus a parcel-image release project.
- Structured prediction: four tutorials on span contracts, constrained decoding, exact-span evaluation, and selective human review, plus a claims-note extraction release project.

Generators: `work/add-machine-learning-self-supervised-20261005.py` and `work/add-machine-learning-structured-prediction-20261005.py`, using `work/ml_fixture_writer_20261005.py`. The new pages also link to prior transfer learning, validation, hard-negative, threshold and serving-cost lessons. Nine links from existing lessons point into these modules. Public bodies have no external research URLs.

## Verification

- `python3 scripts/check-ai-data-content.py`: passed; 442 AI & Data articles, 132 Machine Learning articles, 4,296 AI & Data internal links.
- `node scripts/check-tutorial-html.mjs`: passed.
- All 11 embedded Python examples compiled and ran with passing assertions.
- New pages contain about 443–509 text words including headings, mistakes and link labels, with 5–10 internal body links each.
- `git diff --check`: passed.
- `python3 scripts/export-ai-data-for-wordpress.py`: 491 draft entries; all 11 new pages present as drafts.
- `npm run build`: passed with the existing client bundle-size advisory.

## Editorial research trail (not in public article bodies)

- https://www.geeksforgeeks.org/machine-learning/self-supervised-learning-ssl/
- https://www.geeksforgeeks.org/machine-learning/self-supervised-learning-for-tabular-data/
- https://www.w3schools.com/aws/genai/aws_prompt_foundation_models.php
- https://arxiv.org/pdf/2002.05709
- https://arxiv.org/abs/2111.06377
- https://openaccess.thecvf.com/content/WACV2022/papers/Huynh_Boosting_Contrastive_Self-Supervised_Learning_With_False_Negative_Cancellation_WACV_2022_paper.pdf
- https://www.geeksforgeeks.org/nlp/conditional-random-fields-crfs-for-pos-tagging-in-nlp/
- https://huggingface.co/docs/course/chapter7/2
- https://aclanthology.org/2021.eval4nlp-1.5.pdf

## Remaining scope

The section is still not exhaustive. Further distinct modules could cover survival models as operational ML, sequence-to-sequence structured generation, active learning, online adaptation, and graph representation release workflows. Live route rendering was not verified in this pass. The WordPress artifact is a draft export; no live publication occurred. No objective humanization detector score was measured.
