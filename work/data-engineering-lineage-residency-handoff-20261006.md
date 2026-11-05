# Data Engineering: runtime evidence and replica controls

Six original pages were added: four lessons and two projects. Public article bodies link only to internal AI Trove lessons. The source material below was used to check technical boundaries; no prose or examples were copied into the tutorials.

## Research checked

- GeeksforGeeks data lineage overview: https://www.geeksforgeeks.org/data-engineering/top-50-data-engineering-interview-questions-and-answers/
- GeeksforGeeks data catalog: https://www.geeksforgeeks.org/data-engineering/what-is-a-data-catalog/
- GeeksforGeeks cross-data-center replication: https://www.geeksforgeeks.org/system-design/cross-data-center-replication/
- OpenLineage run and job lineage facets: https://openlineage.io/docs/spec/facets/job-facets/lineage/
- OpenTelemetry context propagation and signals: https://opentelemetry.io/docs/concepts/context-propagation/ and https://opentelemetry.io/docs/concepts/signals/
- Amazon S3 replication deletion behavior: https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication-what-is-isnot-replicated.html
- Amazon S3 delete-marker replication: https://docs.aws.amazon.com/AmazonS3/latest/userguide/delete-marker-replication.html
- Google Cloud processing locations: https://docs.cloud.google.com/sensitive-data-protection/docs/specifying-location

W3Schools, BeginnersBook and CodingNomads were searched, but did not provide the detailed runtime lineage, versioned replica deletion and residency controls required for this batch. Primary documentation resolved those points.

## Scope and checks

- Runtime lineage and incident evidence: exact input/output generations, committed-run boundaries, bounded telemetry labels, and a missing-revenue incident project.
- Residency and replica erasure: placement gates covering processing and diagnostic copies, versioned replica deletion and restore guards, and a regional erasure proof project.
- Every new page has five substantive sections, executable Python, performance and operating cost, Common Mistakes, and at least seven internal lesson links.
- Twelve existing pages link to the new topics. Both curriculum and project hubs include the new lessons and projects.
- `scripts/check-ai-data-content.py`, `scripts/check-html-content.py`, six Python examples and `git diff --check` passed.
- WordPress reported 20 imported/updated entries with zero failures.
- The Cloudflare fallback snapshot contains 4,212 published entries, including the six new pages.
- The production Pages build passed; Cloudflare reported successful deployment of 59 assets.
- Cloudflare accepted a targeted purge of the two CMS entry API prefixes.
- All six live routes rendered their expected headings and Common Mistakes sections without page errors. The live tutorial showed both modules, the project hub showed 11 projects, and an older lineage page linked to the new run-scoped lesson.

## Remaining coverage

Additional distinct modules could examine statistical data-quality drift, privacy-safe lineage aggregation, multi-tenant query admission and schema migration at very large table scale. Each needs a concrete failure case and validation code before publication.
