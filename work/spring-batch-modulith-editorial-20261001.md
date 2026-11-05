# Spring Batch and Modulith editorial handoff

The five user-preferred pages concern Java or `LinkedList`; they do not establish Spring Batch or Modulith behavior. Their order was respected during triage, then Spring's own documentation was used for these Spring-specific claims. No source URL appears in the new public tutorial bodies.

Primary checks on 2026-10-01:

- Spring Batch reference: https://docs.spring.io/spring-batch/reference/
- Chunk configuration: https://docs.spring.io/spring-batch/reference/step/chunk-oriented-processing/configuring.html
- Reader and writer stream registration: https://docs.spring.io/spring-batch/reference/step/chunk-oriented-processing/registering-item-streams.html
- Job configuration and identity: https://docs.spring.io/spring-batch/reference/job/configuring-job.html
- Spring Modulith reference: https://docs.spring.io/spring-modulith/reference/
- Modulith verification: https://docs.spring.io/spring-modulith/reference/verification.html
- Modulith events: https://docs.spring.io/spring-modulith/reference/events.html

The isolated Batch project uses Boot 4.0.8, Batch 6.0.5, Java 21 target and H2. Its two tests prove that an earlier two-row chunk stays committed when the next chunk fails, that a same-identity restart completes a four-row import with a key-based writer, and that a completed identity rejects a duplicate launch. The failed execution's saved reader count was two, but the local restart revisited committed rows; a plain INSERT failed with a duplicate key. H2 MERGE makes that particular replay safe. It does not prove process-crash recovery, another database's upsert behavior, or exactly-once external side effects.

The isolated Modulith project uses Boot 4.0.8, Modulith 2.0.8 and Java 21 target. Its two tests prove that a dependency on a neighboring root-package API passes and a dependency on a public `internal` class fails verification. It does not start a Spring context, test a sliced module, persist an event publication or send to a broker.

The eight new lessons distinguish checked behavior from unexecuted design sketches. The fourteen-question browser quiz tests comprehension; it is not a graded credential. Remaining editorial and engineering work includes durable Batch repository and process-restart checks, database-specific upsert conflict policy, skip/retry tests, a running Modulith module test, and event-publication registry recovery. Wider Spring Cloud and Spring AI infrastructure tests remain separate gaps.
