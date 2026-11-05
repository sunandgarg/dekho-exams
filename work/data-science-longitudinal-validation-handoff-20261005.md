# Data Science longitudinal survival validation — editorial handoff

Six new local-fixture articles cover observation timing, counting-process records, censoring support, IPCW Brier scoring, temporal validation, and an applied review project. The article bodies contain original explanations and examples with internal AI Trove links only. The WordPress export remains a draft; no live publication was performed.

Research checked on 2026-10-05. These URLs are retained here for editorial verification and are not part of public tutorial bodies:

- Preferred-site topic survey: https://www.geeksforgeeks.org/data-science/cox-proportional-hazards-model/
- Time-varying interval format and fitting contract: https://lifelines.readthedocs.io/en/latest/Time%20varying%20survival%20regression.html
- Time-varying fitter API: https://lifelines.readthedocs.io/en/stable/fitters/regression/CoxTimeVaryingFitter.html
- IPCW Brier definition and follow-up support: https://scikit-survival.readthedocs.io/en/stable/api/generated/sksurv.metrics.brier_score.html
- External and temporal prediction-model validation principles: https://pmc.ncbi.nlm.nih.gov/articles/PMC4297220/

Validation: all six extracted Python examples executed; all new internal links resolved; `check-ai-data-content.py`, `check-tutorial-html.mjs`, `git diff --check`, export, and `npm run build` returned success. Wrangler emitted an EPERM warning when trying to write a debug log outside the sandbox, although the build exited successfully.
