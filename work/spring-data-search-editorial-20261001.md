# Spring Data and method security batch — editorial handoff

Added 10 original lessons: five Spring Data MongoDB topics (optimistic locking, tenant-scoped unique indexes, transactions, bulk writes, change-stream recovery), three Spring Data Elasticsearch topics (refresh visibility, sequence conflicts, index-alias rollout), and two method-security topics (proxy boundary and post-invocation side effects). The Java LinkedList pages in the supplied preferred list do not describe these Spring contracts. Public tutorial bodies contain internal links only; source URLs stay in this private editorial record.

Official behavior and API checks:

- MongoDB CRUD, bulk and optimistic locking: https://docs.spring.io/spring-data/mongodb/reference/mongodb/template-crud-operations.html
- MongoDB sessions and transactions: https://docs.spring.io/spring-data/mongodb/reference/mongodb/client-session-transactions.html
- MongoDB index creation: https://docs.spring.io/spring-data/mongodb/reference/mongodb/mapping/mapping-index-management.html
- MongoDB change streams: https://docs.spring.io/spring-data/mongodb/reference/mongodb/change-streams.html
- Elasticsearch repository index creation: https://docs.spring.io/spring-data/elasticsearch/reference/elasticsearch/repositories/elasticsearch-repositories.html
- Elasticsearch index operations and sequence metadata: https://docs.spring.io/spring-data/elasticsearch/docs/current/api/org/springframework/data/elasticsearch/core/IndexOperations.html and https://docs.spring.io/spring-data/elasticsearch/docs/current/api/org/springframework/data/elasticsearch/core/query/SeqNoPrimaryTerm.html
- Method security: https://docs.spring.io/spring-security/reference/servlet/authorization/method-security.html

These are implementation sketches, not compiled MongoDB or Elasticsearch applications. The existing Spring kit tests do not execute them. Remaining work: container-backed conflict, transaction, unique-index, bulk-failure, change-stream replay, search-refresh, alias-cutover, and method-security proxy tests; exact dependency-version compatibility; operational backfill and rollback drills. No claim of full ecosystem coverage or AI-detection performance is made.
