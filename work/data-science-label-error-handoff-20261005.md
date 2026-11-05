# Data Science outcome-label error batch

Added five original tutorials and one applied project: validation-subsample design, group-specific sensitivity and specificity, binary-rate correction, differential error in group contrasts, an assumption grid tied to decisions, and a deadline-breach label audit. The five tutorials have a new Data Science hub module, the project is in both project listings, and six earlier pages now link into this sequence. Public bodies contain no external citations or URLs.

Local fixture `published` status supports local preview. The WordPress export remains draft-only; nothing was published live.

## Research used for technical verification (internal only)

- Preferred introductory sites were checked first for measurement error, confusion matrices, sensitivity and specificity. Relevant pages included https://www.geeksforgeeks.org/data-science/endogeneity-in-data-science/ and https://www.geeksforgeeks.org/machine-learning/difference-between-sensitivity-and-specificity/ .
- Measurement-error theory and validation designs: https://pmc.ncbi.nlm.nih.gov/articles/PMC7450672/
- Binary outcome misclassification and validity indices: https://pmc.ncbi.nlm.nih.gov/articles/PMC7176121/
- Differential outcome error across groups: https://pmc.ncbi.nlm.nih.gov/articles/PMC10237297/
- Quantitative bias analysis and validation-data limitations: https://www.bmj.com/content/385/bmj-2023-076365

## Verification

- Six extracted Python examples executed successfully.
- `python3 scripts/check-ai-data-content.py`: passed; 141 Data Science article rows, 2,888 AI/Data internal links.
- `node scripts/check-tutorial-html.mjs`: passed.
- `git diff --check`: passed.
- `python3 scripts/export-ai-data-for-wordpress.py`: 362 draft entries.

## Remaining scope

The Data Science curriculum is not exhaustive. Future deep topics include partial identification and bounds, heterogeneous effects with uncertainty, capacity-constrained decisions, and evaluation after deployment. The label-error pages provide descriptive corrections and scenario analyses; they do not claim to resolve confounding or supply formal intervals from a small validation audit.
