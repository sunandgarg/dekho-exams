# Data Engineering: event evolution and regional recovery

This batch adds eight original pages: six lessons and two projects. Public article bodies use internal AI Trove links and contain no external source links. The pages were written from concepts checked against the sources below, without copying their prose or examples.

## Research checked

- GeeksforGeeks data-engineering interview topics, schema evolution: https://www.geeksforgeeks.org/data-engineering/top-50-data-engineering-interview-questions-and-answers/
- GeeksforGeeks data catalog: https://www.geeksforgeeks.org/data-engineering/what-is-a-data-catalog/
- GeeksforGeeks schema versioning: https://www.geeksforgeeks.org/dbms/what-is-schema-versioning-in-dbms/
- GeeksforGeeks cross-data-center replication: https://www.geeksforgeeks.org/system-design/cross-data-center-replication/
- Confluent schema registry evolution: https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html
- Apache Iceberg reliability and concurrent writes: https://iceberg.apache.org/docs/1.4.2/reliability/
- AWS recovery drill guidance: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_dr_tested.html
- AWS database disaster-recovery strategy: https://docs.aws.amazon.com/prescriptive-guidance/latest/strategy-database-disaster-recovery/defining.html
- AWS global-table consistency and conflict resolution: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/globaltables_HowItWorks.html

W3Schools, BeginnersBook and CodingNomads were searched for the advanced topics in this batch. The deeper claims were checked against primary documentation where those sources lacked detail.

## Scope and checks

- Event contracts and concurrent tables: transitive schema compatibility, event envelopes and tombstones, optimistic commit conflicts, and an order-event migration project.
- Regional recovery and query serving: RPO/RTO and complete-generation lag, writer fencing and source positions, serving-index freshness, and a regional analytics recovery project.
- Each new page has five substantive sections, executable Python, performance and operating cost, Common Mistakes, and five linked published routes.
- Twelve existing pages link into the new pages; the curriculum and project hub include both modules and projects.
- `scripts/check-ai-data-content.py`, `scripts/check-html-content.py`, all eight Python examples and `git diff --check` passed before publishing.
- WordPress importer reported 22 imported/updated entries and zero skipped/failed.
- The Cloudflare outage fallback snapshot now contains 4,206 published entries and exactly matches the 22 imported rows.
- The production Pages build passed and Cloudflare reported a successful deployment of all 59 assets.
- The two CMS REST path prefixes were purged from Cloudflare cache after deployment.
- All eight new article routes loaded on `aitrove.in` with their expected headings and Common Mistakes sections. The live tutorial showed both new modules; the project hub showed all nine projects, including the two new ones. An older schema-compatibility page linked back to the new registry lesson.

## Remaining coverage

Further distinct modules could cover observability instrumentation and trace-based lineage, data residency in cross-region replication, deletion proof across old replicas, and cost-aware query-serving tiers. Each needs its own contract, failure exercise, and executable example before publication.
