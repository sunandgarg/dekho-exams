# Spring configuration and versioned migration pass — 30 September 2026

Spring and Spring Boot remain one separate subject under `/spring/spring-boot`, outside the Java curriculum. This pass adds eight original articles: three on file-backed Boot configuration, four on versioned migration behavior and ownership, and one release-trace exercise. The Spring operations quiz adds twelve explained questions. All new lessons are linked from their section curricula; related Java and earlier Spring pages point to the new checked material.

## Checked behavior

- `BootRelaySettingsTest` now reads a real temporary `application.properties` with `spring.config.additional-location`. The file overrides the programmatic defaults; a command-line batch-size argument overrides that one file key while the file-backed timeout stays bound. The existing invalid-value check still rejects startup.
- `FlywayReceiptMigrationTest` applies committed V1, V2 and V3 SQL resources through test-scoped Flyway on H2 2.3.232. It checks old-writer compatibility at V2, backfill and old-writer rejection at V3, three versioned history entries, no work on a repeat `migrate()`, and validation failure after a deliberate checksum mismatch in an isolated test database.
- The runnable `ReceiptApplication` does not run Flyway at startup. The test resources live at `db/relay-migration`, not the default production migration location. The Flyway dependency has test scope.

The Spring source kit now has 123 passing Maven tests. The site build, tutorial HTML checker and Spring content checker pass. Spring content inventory: 143 articles, 10 section hubs, 4 quizzes with 97 questions, 1,210 body links and no curriculum orphans. The separate Java checker also verifies the reverse link from its versioned-migrations page.

## Research and editorial boundary

The requested references were reviewed in the given order: [Oracle LinkedList API](https://docs.oracle.com/javase/8/docs/api/java/util/LinkedList.html), [GeeksforGeeks Java tutorial](https://www.geeksforgeeks.org/java/java/), [W3Schools LinkedList](https://www.w3schools.com/java/java_linkedlist.asp), [BeginnersBook LinkedList](https://beginnersbook.com/2013/12/linkedlist-in-java-with-example/) and [CodingNomads linked lists](https://codingnomads.com/java-301-linked-lists). These are Java language and collection references, not evidence for Spring configuration or migration behavior. The Spring boundary was checked against the [Spring Boot external configuration reference](https://docs.spring.io/spring-boot/reference/features/external-config.html), [Spring Boot database initialization reference](https://docs.spring.io/spring-boot/how-to/data-initialization.html) and [Flyway Java API documentation](https://documentation.red-gate.com/fd/quickstart-api-184127575.html). Lesson prose and fixture names are original to AI Trove; research sources were not copied into article bodies.

## Remaining work

1. Run the same SQL on the selected production database engine and measure DDL locks, index effects and large-table backfill cost. H2 cannot establish these properties.
2. Choose a migration owner: a deployment job or the application's startup. Add the needed runtime Flyway/database dependencies and readiness gate only after that choice. The current kit has no production migration wiring.
3. Test a mixed-version rollout with actual old and new processes across V2 and V3, plus interruption/restart and a reviewed repair procedure for failed non-transactional DDL.
4. Test process environment variables, mounted files, secret rotation and missing-location policy in the intended hosting environment. The new file tests use a local JUnit temporary directory.
5. Spring coverage is broad, not an exhaustive reference for every Spring module or release. Further lessons need individual technical review and executable contracts before publication. Search visibility and rankings require a live domain, crawl/index access and observed user-query data; content volume alone cannot guarantee either.
