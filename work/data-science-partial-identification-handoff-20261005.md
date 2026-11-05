# Data Science partial-identification batch

Added five original tutorials and one applied project on outcome bounds: an assumption ledger, worst-case binary-rate bounds, effect bounds with differential attrition, restricted missing-risk scenarios, action thresholds and follow-up value, and a routing-policy review. The tutorials have a new Data Science hub module. The project is in both project listings. Six existing pages link into this sequence, and the new pages crosslink to related lessons. Public bodies contain no external sources or URLs.

Local fixture `published` status serves local preview. The WordPress export is draft-only; no live publication was performed.

## Research used for technical verification (internal only)

- Preferred introductory sources were checked first for missing data, outcome support and distinction between estimation intervals and data gaps: https://www.geeksforgeeks.org/data-science/listwise-deletion-in-missing-data/ and https://www.w3schools.com/statistics/statistics_estimation.php .
- Worst/best-case missing-outcome bounds in randomized studies: https://pmc.ncbi.nlm.nih.gov/articles/PMC7337281/
- Missing outcomes and reporting limitations: https://pmc.ncbi.nlm.nih.gov/articles/PMC4203602/
- Partial identification with missing data: https://doi.org/10.1016/j.ijar.2004.10.006

## Verification

- Six extracted Python examples executed successfully.
- `python3 scripts/check-ai-data-content.py`: passed; 147 Data Science article rows, 2,949 AI/Data internal links.
- `node scripts/check-tutorial-html.mjs`: passed.
- `git diff --check`: passed.
- `python3 scripts/export-ai-data-for-wordpress.py`: 368 draft entries.

## Remaining scope

The Data Science curriculum remains open-ended. High-value next modules include heterogeneous effects with uncertainty, decisions under capacity constraints, measurement error in continuous predictors, and monitoring effect estimates after deployment. The new intervals describe identification under stated assumptions; they are not confidence intervals or causal estimates absent a valid assignment design.
