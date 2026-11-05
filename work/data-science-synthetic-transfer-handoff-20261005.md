# Data Science synthetic-control and transfer batch

Added six original local fixture pages: donor eligibility and pre-fit; constrained weight search; placebo fit ratios; donor/window sensitivity; target-population standardization; and a single-branch policy-transfer review project. The five tutorials are in the new Data Science hub module. The project is in both project listings. Six earlier pages now link into this sequence, and each new page links to related internal lessons.

The public article bodies contain no external citations or source URLs. The examples and scenario values are original to this batch. The local fixture uses `status=published` for preview, while the WordPress export remains draft-only; no live publishing was performed.

## Research used for technical verification (internal only)

- Preferred introductory research: https://www.geeksforgeeks.org/data-science/difference-in-differences-did/ and relevant topic searches across GeeksforGeeks, W3Schools, BeginnersBook and CodingNomads. The narrow synthetic-control and transportability details required specialist sources.
- Synthetic-control practice and pre-fit: https://ftp.aeaweb.org/articles?id=10.1257%2Fjel.20191450 and https://pmc.ncbi.nlm.nih.gov/articles/PMC8634614/
- Convex weights and treatment-unit setup: https://arxiv.org/abs/1610.07748
- Placebo and pre-fit ratio diagnostics: https://pmc.ncbi.nlm.nih.gov/articles/PMC10981189/
- Target-population effect modification and transport: https://pmc.ncbi.nlm.nih.gov/articles/PMC6049838/ and https://pmc.ncbi.nlm.nih.gov/articles/PMC5466356/

## Verification

- `python3 scripts/check-ai-data-content.py`: passed; 129 Data Science article rows and 2,766 AI/Data internal links.
- `node scripts/check-tutorial-html.mjs`: passed.
- Extracted and executed each of the six Python examples: passed.
- `git diff --check`: passed.
- `python3 scripts/export-ai-data-for-wordpress.py`: 350 draft entries.

## Scope still open

This batch covers one single-unit causal design and a first transport calculation. The Data Science curriculum is not exhaustive. A future batch could cover interrupted time series with concurrent controls, partial identification and bounding, measurement-error sensitivity, heterogeneity estimation with uncertainty, and decision analysis under capacity constraints. Each needs a separate design and concrete examples rather than a title-only page.
