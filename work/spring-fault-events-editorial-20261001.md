# Spring fault handling and module events editorial handoff

The user's five preferred links are Java and LinkedList material. They were checked first but do not establish Spring Batch 6 or Modulith 2 behavior. This pass verified framework-specific details against official Spring documentation. Public tutorial bodies have internal lesson links and no external source URLs.

Primary checks on 2026-10-01:

- Spring Batch skip logic: https://docs.spring.io/spring-batch/reference/step/chunk-oriented-processing/configuring-skip.html
- Spring Batch retry logic: https://docs.spring.io/spring-batch/reference/step/chunk-oriented-processing/retry-logic.html
- Spring Modulith module testing: https://docs.spring.io/spring-modulith/reference/testing.html
- Spring Modulith events and registry: https://docs.spring.io/spring-modulith/reference/events.html

The Boot 4.0.8 / Batch 6.0.5 H2 source project now runs five tests: two earlier chunk and identity contracts and three new fault-policy contracts. The new tests prove one accepted processor skip, failure on the second invalid row when the limit is one, recovery from one temporary exception, and failure after the temporary exception persists through the retry budget. These are local H2 outcomes. They do not cover a production deadlock, persistent reject ledger, two-process crash restart or a remote side effect.

The Boot 4.0.8 / Modulith 2.0.8 source project now runs four tests: two package-architecture checks and two inventory module-slice checks. The module slice starts a Spring context, excludes the neighboring dispatch bean, observes one matching ReceiptReserved event for an accepted command, and sees no success event for a rejected one. Inventory state is an in-memory map. The slice does not establish database atomicity, a persistent event publication registry, asynchronous listener completion, process recovery or broker delivery.

Eight original semantic-HTML lessons were added. Older Batch and Modulith lessons were corrected to distinguish the new checked behavior from the remaining design sketches. The durable restart, reconciliation and registry recovery lessons are plans for tests not yet implemented; their metadata says so. No AI-detection score or exclusive ownership of framework facts is asserted.
