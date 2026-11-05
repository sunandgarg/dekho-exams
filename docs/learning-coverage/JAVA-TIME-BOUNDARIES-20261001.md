# Java calendar and timestamp contracts — editorial handoff

Ten original Java tutorials were added to the Advanced Java module, "Calendar and timestamp contracts." Each contains a runnable Java 8 program, verified output, cost and ownership notes, Common Mistakes, and internal links. Existing date-time, zone-transition, strict-parsing, and clock lessons link back to this batch.

New `/java/` paths: `duration-versus-period-dst`, `zoned-zone-conversion`, `offsetdatetime-same-instant`, `yearmonth-end-of-month`, `formatter-week-year-boundary`, `instant-epoch-millis-truncation`, `localdate-exclusive-range`, `offset-validated-against-zone`, `duration-negative-components`, and `period-month-end-arithmetic`.

The five user-prioritized LinkedList and Java-learning sites were reviewed for the wider curriculum inventory. They are not source text or code for this time-boundary batch. Primary API contract checks for this batch were:

- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/ZonedDateTime.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/LocalDateTime.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/Duration.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/Period.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/format/DateTimeFormatter.html

The public lesson bodies contain no external URLs. These programs use fixed values to make output reproducible, but regional time-zone rules come from the JDK's time-zone database. Release checks should rerun the programs against supported JDKs after time-zone database updates. Java API facts are not exclusive property, and an AI-detector score is not established by this check.

Remaining Java work is open ended: broader database and network incident coverage, real filesystem fault injection, supported-JDK and operating-system matrices, larger concurrency stress tests, additional DSA proofs and adversarial cases, and more graded exercises and quizzes. These ten programs establish their stated local behavior, not production scheduling or persistence behavior.
