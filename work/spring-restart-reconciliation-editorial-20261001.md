# Spring Batch restart and rejected-row editorial handoff

This file records the research and local proof boundary for editors. It is not a public lesson or a source for copied prose.

## Source triage

The five priority URLs in the user request describe Java or `LinkedList`, not Spring Batch. They can inform Java prerequisites but do not establish the Spring restart behavior in this pass:

1. https://docs.oracle.com/javase/8/docs/api/java/util/LinkedList.html
2. https://www.geeksforgeeks.org/java/java/
3. https://www.w3schools.com/java/java_linkedlist.asp
4. https://beginnersbook.com/2013/12/linkedlist-in-java-with-example/
5. https://codingnomads.com/java-301-linked-lists

For the Spring-specific behavior, inspect the primary reference and API pages:

- https://docs.spring.io/spring-batch/reference/job/configuring-job.html
- https://docs.spring.io/spring-batch/reference/step/chunk-oriented-processing/restart.html
- https://docs.spring.io/spring-batch/reference/job/advanced-meta-data.html
- https://docs.spring.io/spring-batch/reference/step/chunk-oriented-processing/configuring.html
- https://docs.spring.io/spring-batch/reference/step/chunk-oriented-processing/intercepting-execution.html
- https://docs.spring.io/spring-batch/reference/api/org/springframework/batch/core/listener/SkipListener.html
- https://docs.spring.io/spring-boot/reference/io/spring-batch.html
- https://docs.spring.io/spring-batch/reference/job/configuring-repository.html
- https://docs.spring.io/spring-batch/reference/job/configuring-infrastructure.html
- https://docs.spring.io/spring-batch/reference/api/org/springframework/batch/core/launch/JobOperator.html
- https://docs.spring.io/spring-boot/4.0/reference/io/spring-batch.html

## Local proof

- `TwoProcessRestartContractTest` starts two separate JVMs against one file-backed H2 database with the Boot 4 JDBC Batch starter. The first records `FAILED` after one committed chunk; the next starts from that recorded state, uses the same identifying manifest parameter and JobInstance ID, then reaches `COMPLETED` with four unique target IDs. It reads the repository tables and checks one persisted instance and two executions. The previous fixture used Boot's in-memory repository, so matching numeric IDs alone were a false positive; this is corrected.
- A second test forcibly kills the first JVM between chunks. The persisted execution remains `STARTED` and an unchanged launch is refused. After the test verifies the old process is dead, `JobOperator.recover` marks it recoverable and a new execution completes under the original instance.
- A third test changes a source row after a recorded failure. A manifest-linked SHA-256 digest blocks the restart before a new Batch execution is made.
- `BatchFaultPolicyContractTest` checks one skipped invalid row, an exceeded skip limit, temporary retry recovery, retry exhaustion and a keyed H2 rejection row from `SkipListener`.
- The tests do **not** probe a crash inside the business-write/metadata-commit window, a competing writer across hosts, input mutation after the digest check, or a live database snapshot. They do **not** cover the target production database, a broker, a review workflow or real private data retention.

## Next proof work

Add a target-database test with a controlled process kill inside the business-write/metadata-commit window and explicit worker fencing. Add an immutable input snapshot and a per-manifest reconciliation ledger. Do not present a universal SQL edit as the recovery method.
