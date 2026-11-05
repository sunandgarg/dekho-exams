The following is the preserved prior-pass snapshot. Current totals and checks are in [THIRD-PASS.md](THIRD-PASS.md).

# Java and Spring: preceding continuation (d391616)

This pass adds eight original Java articles and eight Spring articles, preserving every prior lesson and quiz bank. Current totals: Java 214 articles, 10 hubs and 14 quizzes (238 routes); Spring & Spring Boot 37 articles, 10 hubs and 3 quizzes (50 routes). There are 288 subject records and 289 reviewed records including the editorial profile. The launch-mode sitemap adds the homepage; the built runtime check records its measured URL count.

Spring & Spring Boot remains one independent subject at /spring/spring-boot. No Spring URL appears in Java module lists. New Spring pages use their own data, core, web, security and production sections; section overview bodies now list the added lessons. Seventeen existing pages gain contextual links to the new material. The coverage map records all written pages and explicitly names unfinished scope.

## Java additions and evidence

- Strict UTF-8 decoding before field parsing.
- Strict calendar-date resolution.
- Whole-field, locale-pinned decimal parsing.
- Bounded primitive-array legacy serialization filtering.
- Shared-arena ownership and close timing.
- Phaser registration and deregistration.
- LinkedList cursor-local editing.
- Lazy interval additions and range-sum queries.

Each article has a complete newly written program, checked output, costs, ownership/input limits and Common Mistakes. Java validation compiles 203 distinct programs/fragments, executes 192 and checks 177 declared outputs on release targets 8, 11, 17, 21 and 25. Dependency-specific JDBC/JUnit/JMH evidence remains recorded in earlier release reports and is not relabelled as standalone JDK execution.

The new lazy range tree passes 60,000 deterministic comparisons against direct array sums, plus 15 additional range/input rejection checks. The oracle uses small bounded values; long-overflow safety is not claimed. Serialization allows only a small primitive int array and bounds the encoded bytes, rather than promising a general untrusted-object sandbox. The arena example joins its worker before closing; it does not prove arbitrary concurrent write safety.

## Spring additions and evidence

JPA managed/detached state; many-to-one lazy/fetch statement counts; versioned stale-write rejection; REQUIRED/REQUIRES_NEW outcomes; AFTER_COMMIT timing; proxy-based method authorization; finite meter tag identities; Reactor demand/cancellation.

The source kit now runs 42 passing Maven tests, including 12 added tests, with no failures, errors or skips. Four existing standalone mains retain exact checked outputs. The package still selects ReceiptApplication as its entrypoint.

The JPA tests exposed and now check a lazy-proxy distinction: direct public-field access does not initialize the proxy in this fixture, while the getter does. Fresh-context traversal records four statements without a fetch join and one with it. Both tests verify the same account total.

Checked dependency baseline: JDK 21, Boot 4.0.8, Framework 7.0.9, Hibernate 7.2.24.Final, Reactor 3.8.7 and Micrometer 1.16.7. These versions come from the actual Maven dependency classpath; they are a pinned learning baseline, not a latest-release claim.

Fixtures live in in.aitrove.contracts, outside the HTTP application's component scan. JPA create-drop runs solely on an isolated in-memory H2 database. The HTTP API still uses its existing in-memory store and labelled fixture identity. JPA teaching classes do not make that API durable. Reactor Core tests do not imply a WebFlux HTTP service; method authority checks do not imply resource ownership; a local meter count does not measure remote telemetry retention. Source archives exclude compiled targets, JDKs, dependency binaries and private configuration.

## Research and writing

The requested coverage sources were reviewed in the requested order: [Oracle LinkedList](https://docs.oracle.com/javase/8/docs/api/java/util/LinkedList.html), [GeeksforGeeks Java roadmap](https://www.geeksforgeeks.org/java/java/), [W3Schools LinkedList](https://www.w3schools.com/java/java_linkedlist.asp), [BeginnersBook LinkedList](https://beginnersbook.com/2013/12/linkedlist-in-java-with-example/), [CodingNomads linked lists](https://codingnomads.com/java-301-linked-lists). Third-party tutorials are curriculum references, not copied prose or renamed examples. Technical claims rely on official contracts and tested behavior.

Primary sources: [CharsetDecoder](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/nio/charset/CharsetDecoder.html), [DateTimeFormatter](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/time/format/DateTimeFormatter.html), [DecimalFormat](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/text/DecimalFormat.html), [ObjectInputFilter](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/io/ObjectInputFilter.html), [Arena](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/foreign/Arena.html), [Phaser](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Phaser.html), [JPA EntityManager](https://jakarta.ee/specifications/persistence/3.2/apidocs/jakarta.persistence/jakarta/persistence/entitymanager), [JPA Version](https://jakarta.ee/specifications/persistence/3.2/apidocs/jakarta.persistence/jakarta/persistence/version), [Hibernate 7.2](https://docs.hibernate.org/orm/7.2/userguide/html_single/), [Spring JPA](https://docs.spring.io/spring-framework/reference/data-access/orm/jpa.html), [Propagation](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/tx-propagation.html), [Transaction events](https://docs.spring.io/spring-framework/reference/data-access/transaction/event.html), [Method security](https://docs.spring.io/spring-security/reference/servlet/authorization/method-security.html), [Micrometer meter identities](https://docs.micrometer.io/micrometer/reference/concepts/meters.html), [Reactor demand](https://projectreactor.io/docs/core/release/reference/coreFeatures/simple-ways-to-create-a-flux-or-mono-and-subscribe-to-it.html).

Public tutorial bodies remain original semantic HTML with deliberate internal links. Research URLs are in this handoff. API facts, syntax, trademarks and open-source dependencies are not claimed as exclusive AI Trove property; no human-authorship or AI-detection guarantee is made.

## Remaining scope

The map retains native linking, wider desktop/Jakarta tracks, target-database recovery/load tests, further algorithms, Spring Data repository/projection work, WebFlux HTTP, OAuth2/OIDC, durable messaging/outbox, remote telemetry and WordPress import/setup. The two subjects are populated curricula, not exhaustive ecosystem coverage. Main merging, production deployment and CMS import have not been performed in this pass.

Current machine-readable evidence is in java-program-check.json, spring-content-validation.json, java-next-boundaries.json, next-links-check.json, browser-check.json and publish-runtime-check.json. The two latter reports are refreshed after final browser/build verification.

Final checks: TypeScript and the production build pass. Browser checks cover 58 screens, 320/390/768-pixel mobile views, all 36 Spring quiz answers and the preserved 16-card homepage, with no page errors. The built runtime contains all 290 eligible sitemap URLs (238 Java, 50 Spring, editorial profile and homepage); all 58 checked page responses contain their canonical tags and structured data. Coverage maps and source downloads remain noindex/nosniff. The source ZIPs contain 222 Java and 27 Spring files. Current body links total 1081, with zero missing/unpublished targets, 52 Java-to-Spring links and 99 Spring-to-Java links. The development preview remains separate from the live site.

Every one of the 16 added lessons also passes its Contents interaction and overflow check at both 320 and 390 pixels (32 additional mobile screens). The final wording makes clear that the range tree requires bounded arithmetic and does not reject long overflow automatically.
