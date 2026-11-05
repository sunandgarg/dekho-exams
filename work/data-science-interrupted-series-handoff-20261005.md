# Data Science interrupted-series batch

Added five original tutorials and one applied review project. The new pages cover the outcome and intervention clock; segmented level and slope changes; a controlled comparison series; seasonality and serial dependence; transition windows and lag sensitivity; and a policy-review packet. The tutorials have their own Data Science hub module. The project appears in the main and project hubs. Six earlier pages now link into the sequence, and the new pages connect to other relevant Data Science lessons.

Public tutorial bodies contain no external citations or source URLs. All fixture examples use original service-queue scenarios and values. The local fixture uses published status for local preview, while the WordPress export remains draft-only; nothing was sent live.

## Research used for technical verification (internal only)

- Preferred introductory sites were checked first. Relevant background: https://www.geeksforgeeks.org/data-science/time-series-regression/ and https://www.w3schools.com/datascience/ds_linear_regression.asp. The narrower design questions required methods literature.
- Segmented level and slope, comparison design, seasonality and autocorrelation: https://pmc.ncbi.nlm.nih.gov/articles/5407170/ and https://pmc.ncbi.nlm.nih.gov/articles/PMC8011057/
- Method comparisons and dependence-aware inference: https://pmc.ncbi.nlm.nih.gov/articles/PMC8235830/ and https://pmc.ncbi.nlm.nih.gov/articles/PMC3828652/
- Controlled interrupted series: https://www.degruyterbrill.com/document/doi/10.1515/em-2018-0010/html

## Verification

- `python3 scripts/check-ai-data-content.py`: passed; 135 Data Science article rows and 2,827 AI/Data internal links.
- `node scripts/check-tutorial-html.mjs`: passed.
- Extracted and executed every new Python example: six passed.
- `git diff --check`: passed.
- `python3 scripts/export-ai-data-for-wordpress.py`: 356 draft entries.

## Remaining scope

The Data Science curriculum is still open-ended. Worth developing as separate, full lessons: partial identification and bounds; measurement-error sensitivity; effect heterogeneity with uncertainty; decision analysis under capacity constraints; and calibration or monitoring of causal estimates after rollout. Avoid turning any of these into unsupported single-number claims.
