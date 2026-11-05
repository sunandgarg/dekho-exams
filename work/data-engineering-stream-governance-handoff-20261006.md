# Data Engineering: streaming state and governed data products

This batch adds ten original pages: eight lessons and two projects. The public article bodies contain only internal AI Trove links. The references below were used to check concepts, not copied as article text.

## Research checked

- GeeksforGeeks: https://www.geeksforgeeks.org/system-design/stream-processing-system-design-architecture/
- GeeksforGeeks: https://www.geeksforgeeks.org/data-engineering/how-do-you-handle-streaming-data-in-a-data-engineering-pipeline/
- GeeksforGeeks: https://www.geeksforgeeks.org/data-engineering/what-is-stream-processing/
- GeeksforGeeks: https://www.geeksforgeeks.org/computer-networks/back-pressure-in-distributed-systems/
- W3Schools: https://www.w3schools.com/aws/aws_cloudessentials_aiml_datapipelines.php
- Apache Flink checkpoints: https://nightlies.apache.org/flink/flink-docs-stable/docs/ops/state/checkpoints/
- Apache Flink large state and backpressure: https://nightlies.apache.org/flink/flink-docs-stable/docs/ops/state/large_state_tuning/
- Apache Flink fault tolerance: https://nightlies.apache.org/flink/flink-docs-stable/docs/learn-flink/fault_tolerance/
- Apache Flink savepoints: https://nightlies.apache.org/flink/flink-docs-stable/docs/ops/state/savepoints/
- Databricks row filters and column masks: https://docs.databricks.com/aws/en/data-governance/unity-catalog/filters-and-masks
- Databricks access control: https://docs.databricks.com/aws/en/data-governance/unity-catalog/access-control/
- AWS analytics cost lens: https://docs.aws.amazon.com/pdfs/wellarchitected/latest/analytics-lens/analytics-lens.pdf
- AWS data lake cost model: https://docs.aws.amazon.com/pdfs/whitepapers/latest/cost-modeling-data-lakes/cost-modeling-data-lakes.pdf

BeginnersBook and CodingNomads were searched for relevant advanced data-engineering coverage; no topic-specific material was used for the advanced claims in this batch.

## Scope and validation

- Four lessons on keyed state, watermark corrections, temporal stream joins and catch-up budgets, plus a recoverable risk-ledger project.
- Four lessons on classification, row and mask policy tests, dataset ownership and cost attribution, plus a governed customer-mart project.
- Every new page has five substantive concept sections, an executable Python example, a performance/operating-cost discussion, Common Mistakes, and five related routes.
- Twelve existing pages gained a directed link to the new work. Both hub curricula and the project listing gained the new modules and projects.
- `scripts/check-ai-data-content.py`, `scripts/check-html-content.py`, each new Python code block, and `git diff --check` passed before publication.
- WordPress importer reported 24 imported or updated entries and zero skipped or failed.
- The Cloudflare fallback snapshot was updated to 4,198 published entries.
- The production Cloudflare Pages build completed and its 59-file upload deployed successfully.
- All ten new public routes were opened on `aitrove.in`; each rendered the expected lesson title and Common Mistakes section. A pre-existing lesson was checked for its new cross-link.
- The main curriculum initially returned an old cached CMS response. A targeted Cloudflare prefix purge of `cms.aitrove.in/wp-json/aitrove/v1/entry` and `.../entries` succeeded. Reloading the public hub then showed both new modules, both new projects, and seven projects in Apply your knowledge.

## Future coverage

The Data Engineering domain is not exhausted. Suitable next modules include privacy-preserving deletion audits across replicas, schema registry migration, multi-region disaster recovery, query serving indexes, lakehouse transaction conflict handling, and platform observability instrumentation. Add these as distinct lessons only after their contracts and executable examples are verified.
