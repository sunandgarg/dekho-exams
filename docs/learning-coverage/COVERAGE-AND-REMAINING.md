# Java, Spring and Python coverage

Java: 264 articles + 10 hubs + 14 quizzes. Spring & Spring Boot: 183 articles + 10 hubs + 9 quizzes. Python: 310 articles + 14 hubs + 23 quizzes.

Spring is a separate subject. No Spring page appears in the Java module lists. Cross-links connect the related contracts. Current counts supersede earlier release snapshots; they do not imply exhaustive coverage.

## Java — Java Tutorial

Overview: /java/java. Written and checked lessons: 42.

Remaining:
- More cross-package nested-type exercises and retained-owner checks. The inner/static ownership fixture covers one bounded case.
- International identifier/confusable policies beyond the bounded ASCII protocol fixture, and more locale/version-specific text tests.
- Wider locale-sensitive input policies, configuration-source precedence across operating-system and deployment sources, and ambiguous local-time input flows; one manual Properties overlay, strict UTF-8, strict dates and full-consumption decimal parsing have bounded fixtures.

## Java — Advanced Java

Overview: /java/advanced-java. Written and checked lessons: 83.

Remaining:
- Wider native ABI, pointer/callback ownership, library/version coverage and hostile-input fuzzing. A scalar C function downcall, confined/shared arena lifetime and a bounded primitive-array serialization filter are checked.
- Full Jakarta and JavaFX tracks and wider Swing applications. Spring & Spring Boot has moved to its own populated subject; it is not a Java module.
- Production database engines: serialization/deadlock faults, pool load tests, multi-deployer schema migrations and recovery. H2 checks are not evidence for another engine.
- Heap-reference-path interpretation for real incidents. Synthetic heap capture and bounded JFR event recording are verified here.
- Representative multi-fork JMH experiments. Earlier smoke checks prove benchmark execution, not performance rankings.
- Real filesystem race and error-injection tests, interruption latency under worker load and remote future failure policies remain. Files.walk close, Thread.interrupted clearing, allOf failure and handle versus whenComplete now have checked fixtures.

## Java — Interview Questions

Overview: /java/java-interview-questions. Written and checked lessons: 11.

Remaining:
- More multi-file code traces and real incident follow-ups.

## Java — Exercises

Overview: /java/java-exercises. Written and checked lessons: 10.

Remaining:
- More difficulty-graded problems and rejection cases.
- Server-judged submissions require an execution service; these exercises run locally.

## Java — Examples

Overview: /java/java-examples. Written and checked lessons: 16.

Remaining:
- More multi-package examples and external-service fault scenarios.

## Java — Quizzes

Overview: /java/java-quizzes. Written and checked lessons: 16.

Remaining:
- Authenticated cross-device attempt storage requires a backend; scores are browser-local.
- Larger application-level trace banks beyond the current 168 questions.

## Java — Projects

Overview: /java/java-projects. Written and checked lessons: 10.

Remaining:
- External HTTP/TLS: certificate-chain rotation/expiry, DNS failures, load and end-to-end service deadlines. Local TLS verifies only its stated fixture.
- Crash-durable, multi-process file publication and database-backed services. The concurrent import fixture preserves the prior file on validation failure; it is not a durability guarantee.
- Deployment and real-service integration testing.
- Crash-durable ZIP extraction and safe filesystem publication, including symlink races.

## Java — Cheatsheet

Overview: /java/java-cheatsheet. Written and checked lessons: 9.

Remaining:
- More API references, release differences and library topics beyond this selected curriculum.

## Java — DSA in Java

Overview: /java/dsa-in-java. Written and checked lessons: 49.

Remaining:
- Ranked/compressed tries and wider graph, string and DP problems with proofs.
- More adversarial large-input tests and language-independent DSA material.
- Compressed tries, further graph/string problems, overflow policies and larger adversarial inputs. Prefix sums, range updates, monotonic stacks/deques, weighted intervals, augmenting matching, residual flow and unit-grid A-star have checked examples; sparse representations and large adversarial workloads remain.

## Java — Java Collections

Overview: /java/java-collections. Written and checked lessons: 48.

Remaining:
- Larger comparator, iterator and nested-mutability exercise sets. Checked fixtures now cover identity-based keys, TreeSet comparator collisions and EnumMap null/order behavior alongside LinkedList cursor edits, checked views, filtering, map remapping and priority-queue ties.
- Distributed ownership and transactional workflows beyond the in-process multi-index fixture. Local collection examples do not establish cross-process behavior.

## Spring & Spring Boot — Spring & Spring Boot Tutorial

Overview: /spring/spring-boot. Written and checked lessons: 32.

Remaining:
- Separately packaged starters, wider classpath combinations and deployment-level startup failures remain. Non-web Boot tests check profile files, required and optional imports, CLI precedence and Flyway startup through V2/V3 with checksum failure. Twelve child-JVM tests now check environment values, CLI precedence, invalid input, two-hop relative imports, local configtree files and failures, and an extensionless properties file. A production deployment mount, secret store, ReceiptApplication runtime migrations, platform identity and live config rotation remain untested.

## Spring & Spring Boot — Spring Core

Overview: /spring/spring-core. Written and checked lessons: 17.

Remaining:
- Real HTTP request/session concurrency, session expiry and storage, container extension points, AspectJ weaving and wider lifecycle failures remain. Request/session proxies, a failed @Async CompletableFuture and one saturated bounded executor have local checks. Void async failure handling, deployment shutdown drain and restart recovery remain. A test-scoped ThreadPoolTaskScheduler now polls local outbox rows and is cancelled cleanly; it is not installed in the runnable application. AFTER_COMMIT, rollback and no-transaction event behavior are checked; broker delivery remains.

## Spring & Spring Boot — Web APIs

Overview: /spring/web-apis. Written and checked lessons: 27.

Remaining:
- Servlet/proxy multipart limits, durable import staging, full CSV parsing, persistent representation versioning and real-server WebFlux load checks remain. A four-test RestClient loopback fixture now checks explicit factory use, one 503 request, a stalled response and a write committed before a timeout with same-key replay. It does not check a production downstream, TLS, proxy, distributed deduplication or concurrent first requests. The earlier JWT/JDBC POST replay also remains sequential.

## Spring & Spring Boot — Data & Transactions

Overview: /spring/data-transactions. Written and checked lessons: 38.

Remaining:
- Target-database plans, large-table backfills, multi-worker races, broker delivery and crash recovery remain. Direct H2 SQL and test-scoped Flyway fixtures check expand/backfill/contract, history and checksum rejection. A separate non-web Boot context applies the versioned files at startup; the runnable ReceiptApplication still has no runtime migration owner or persistent receipt repository.

## Spring & Spring Boot — Security

Overview: /spring/security. Written and checked lessons: 15.

Remaining:
- OAuth2/OIDC login, remote issuer/JWKS rotation, actual tenant membership and token assignment, session lifecycle, credential recovery, rate limits and a real identity store remain. The upload fixture ignores a traversal filename, and the runnable app now permits nested health paths while leaving the API authenticated. Local JWT contexts check tenant-scoped reads and writes; the stateless bearer POST fixture differs from the runnable Basic-auth application with CSRF. No deployed gateway or target-database ownership proof exists.

## Spring & Spring Boot — Testing

Overview: /spring/testing. Written and checked lessons: 17.

Remaining:
- Target-database, proxy, deployment and crash/restart tests remain. Local checks cover multipart rejection, loopback readiness, JWT tenant writes, relay transitions, scheduled H2 polling, a two-thread H2 claim race and four RestClient loopback cases. Eight Boot settings tests and twelve child-JVM process tests check config sources and failures; two direct SQL, two direct Flyway and two Boot Flyway tests cover local migration behavior. No production migration runner, broker, remote provider or target-engine release matrix is tested.

## Spring & Spring Boot — Production

Overview: /spring/production. Written and checked lessons: 18.

Remaining:
- Graceful shutdown, readiness withdrawal, ingress drain and worker stop are now explained as release contracts, but no process-signal or platform-routing test has run. Local HTTP health checks, test-only scheduled polling and lease states are checked; ReceiptApplication has no deployed worker, broker or real dependency indicator. Remote metrics, target-database behavior and restart recovery remain.

## Spring & Spring Boot — Exercises

Overview: /spring/exercises. Written and checked lessons: 10.

Remaining:
- Larger graded traces and application exercises remain. The settings/schema and new file/Flyway release traces ask for startup values, migration history and old/new writer states from checked local fixtures. A hosted judge needs an execution backend.

## Spring & Spring Boot — Quizzes

Overview: /spring/quizzes. Written and checked lessons: 9.

Remaining:
- Wider release-specific and application traces, plus authenticated cross-device results, remain. Nine browser-local banks contain 157 explained questions, including profile and import behavior, Flyway startup, shutdown budgets, worker leases, checked RestClient timeouts and replay, JWT tenant commands and health-probe separation.

## Spring & Spring Boot — Projects

Overview: /spring/projects. Written and checked lessons: 9.

Remaining:
- Move the JWT/JDBC command, multipart intake and chosen migration owner into the runnable API with real identity, durable staging, target-database tests, a scheduled relay, transport adapter and idempotent consumers. The new release-rehearsal project specifies process, ingress and broker tests but does not execute them. ReceiptApplication still uses in-memory receipts and fixture Basic credentials. Concurrent requests, crashes and operational recovery remain untested.

## Python — Python Tutorial

Overview: /python/python-programming-language-tutorial. Written and checked lessons: 39.

Remaining:
- Broader interpreter migrations, real runtime/platform matrices and larger application refactors. Optimized assertion removal and positional/keyword-only binding now join input validation, callable dispatch, import side effects and bounded recursion.

## Python — Data Types & Collections

Overview: /python/data-types. Written and checked lessons: 31.

Remaining:
- Grapheme-aware editing, confusable identifier policy and comparative memory measurements remain. Exact rational input, enum alias domains and named-zone local-time candidate classification now join shared buffers, ordered maps, NFC and fold; deployed timezone-data updates and user-choice flows need separate checks.

## Python — Advanced Python

Overview: /python/advanced-python. Written and checked lessons: 40.

Remaining:
- Broader metaclass composition/plugin unloading, OS-specific process-tree/output limits, free-threaded builds and real network cancellation remain. Cleanup transfer, nested error partitioning, first-argument type dispatch and unsupported rich comparisons join generator, shield and condition contracts.
- Thread offload, cached-property invalidation and gather sibling lifetime have checked examples; worker cancellation, concurrent first reads and real side-effect recovery still need integration fixtures.
- Two tee readers and an expired asyncio timeout now have checked examples; unbounded iterator lag and deployment-level deadlines still need workload tests.

## Python — Interview Questions

Overview: /python/python-programming-language-tutorial/interview. Written and checked lessons: 14.

Remaining:
- More database and scheduler traces with independent reviewer rubrics. Mutable hash-key assumptions and exception suppression now join cancellation cleanup, WAL snapshots, descriptors, identity/default and iterator reviews; no interview-success claim is made.

## Python — Exercises

Overview: /python/exercises. Written and checked lessons: 17.

Remaining:
- More larger-input/failure-injection tasks, reviewer rubrics and hosted execution remain. Matching feasibility is checked separately from exhaustive small-case optimality; endpoint classification, reconciliation and windows are also covered. An online judge needs an execution service.
- Stable merge, run-length encoding and submitted DAG orders now have checked exercises; hosted grading, streaming input and large adversarial workloads remain.

## Python — Examples

Overview: /python/examples. Written and checked lessons: 27.

Remaining:
- Absolute transport deadlines, key rotation/freshness policy, shared deployment filesystems and target-database isolation remain. Local partial-frame/EOF checks, spool limits and inner savepoint rollback now join encoding, archive and writer fixtures; socket timeouts are not whole-operation deadlines.
- Sorted-feed merging and SQLite foreign-key enforcement have local fixtures; production connection setup, migrations and large-stream limits remain.

## Python — Quizzes

Overview: /python/quizzes. Written and checked lessons: 23.

Remaining:
- More release-specific questions, spaced review and authenticated cross-device storage remain. Twenty-two banks contain 264 explained questions; results stay in the browser.

## Python — Projects

Overview: /python/projects. Written and checked lessons: 14.

Remaining:
- Deployment clock/identity, unique claim-token generation, larger worker contention, recipient deduplication and crash/power-loss recovery remain. Conditional lease renewal now checks current token, strict unexpired ownership and forward extension through two SQLite connections. This does not establish external exactly-once delivery or production multi-engine behavior.

## Python — Cheatsheet

Overview: /python/cheatsheet. Written and checked lessons: 6.

Remaining:
- Broader standard-library/typing references, release guidance and measured operation costs remain. Path/iterator ownership now joins static annotations versus runtime validation, input/sequence, collection ownership and exception cleanup reminders.

## Python — DSA in Python

Overview: /python/dsa-in-python. Written and checked lessons: 46.

Remaining:
- Further graph/string problems, ranked/payload compressed indexes and measured large-input profiling remain. Mutable compressed-edge insertion/deletion now preserves terminal prefixes with a plain-set state oracle; augmenting matching and weighted scheduling use exhaustive small-case oracles alongside the earlier graph, path and sequence fixtures.
- All-pairs paths and residual max flow have small-graph reference checks; larger graph stress, sparse representations and full algorithm breadth remain.
- A-star on a bounded unit-cost grid and Fenwick prefix totals have small-case reference checks; weighted heuristics and large-input profiling remain.

## Python — Packaging & Tools

Overview: /python/packaging. Written and checked lessons: 12.

Remaining:
- Dependency resolution, runtime/platform matrices, binary wheels, registry publication and release automation remain. A RECORD member check and import-origin inspection now join bounded artifact-byte verification, but the trust expectation still needs an authenticated release path; local checks do not prove supply-chain authenticity.
- Entry-point discovery and explicit version acceptance now have local fixtures; signed distribution provenance and a release registry remain.

## Python — Data Analysis

Overview: /python/data-analysis. Written and checked lessons: 25.

Remaining:
- Measured large-data budgets, scientific/ML specialization, dependence-aware uncertainty and model deployment remain. Paired sample/population covariance and declared matrix-axis validation now join quantiles, temporal folds and train-only transforms; descriptive estimates do not establish causation or predictive quality.
- As-of joins and finite-value gating now have checked local examples; larger memory budgets and production data-lineage checks remain.
- One-to-one join validation and missing-key grouping have checked local examples; source-lineage review and measured large-data budgets remain.

## Python — Web Applications

Overview: /python/web-applications. Written and checked lessons: 23.

Remaining:
- Real identity/tenant authentication wired into persistent list/create handlers, production concurrency/backfills, deployment/proxy checks and async web stacks remain. Narrow target allowlists and conditional ETag responses join local upload/DB constraints; parsing is not request authorization and a cache validator is not access permission.
- A local If-Match write demonstrates stale revision rejection; real identity, tenant scope and atomic persistent compare-and-update remain.

## Python — Testing & Quality

Overview: /python/testing. Written and checked lessons: 16.

Remaining:
- Whole-project mutation tooling, real CI/runtime matrices, whole-project typing, integration environments and controlled fault campaigns remain. Fake clocks, metamorphic relations, patch lookup, autospec and temporary cleanup now join selected mutants, grammar/runtime checks, Hypothesis and failure tests; traced allocations are not whole-process RSS or native-buffer accounting.

## Launch work

- WordPress plugin/content import and verified CMS origin
- Purchased domain, canonical origin and DNS
- Editorial review, production indexability switch and deployed recheck
- Authenticated progress and hosted code judging need backend services
