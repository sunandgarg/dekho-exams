# Java and independent Spring curriculum: current pass

This pass adds 20 original articles: 12 Java and 8 Spring. It preserves the earlier lessons and quiz banks. Current totals are Java 226 articles, 10 section hubs and 14 quizzes (250 routes); Spring & Spring Boot 45 articles, 10 hubs and 3 quizzes (58 routes). The two-subject export has 308 records; the reviewed export adds the editorial profile for 309. These describe the written curriculum, not exhaustive Java or Spring ecosystem coverage.

Spring & Spring Boot remains one independent subject at /spring/spring-boot. No Spring URL is in a Java module list. Contextual cross-links connect prerequisites and application boundaries. Twenty-three existing pages receive links to the new articles; Spring overview bodies list every lesson from their preserved modules. The map records written and unfinished scope per section.

## Java additions

- Native Linker: canonical C signature, scalar downcall and rejected integer boundary.
- Flow: explicit demand, completion and failure observation.
- LinkedHashMap LRU: access order and bounded entry count.
- NavigableMap: predecessor lookup, live range and copied snapshot.
- ByteBuffer: protocol order, view state and exact header size.
- CRC32: accidental-change detection with no authenticity claim.
- MessageFormat: apostrophe and placeholder grammar.
- CountDownLatch: completion obligations including worker failures.
- Records with arrays: defensive copies and generated equality limits.
- Z search: overlapping matches and a separator outside the UTF-16 input alphabet.
- Undirected bridges: edge identity for parallel links and self-loops.
- Matrix-chain interval DP: fixed-order grouping and bounded arithmetic.

Each has a complete new program, checked output, stated release, input/ownership limits, costs, Common Mistakes and connected lessons. Java verification compiles 215 distinct programs/fragments, executes 204 and checks 189 displayed outputs on release targets 8, 11, 17, 21 and 25. Existing JDBC/JUnit/JMH dependency evidence remains in its earlier named reports; these programs are not relabelled as standalone JDK execution.

The native fixture requires its manifest runtimeFlags value, --enable-native-access=ALL-UNNAMED, for the source kit's classpath invocation. It checks the local C int carrier and rejects Integer.MIN_VALUE before calling C abs. This grants native access; it is not a sandbox, a wider pointer/callback example or evidence of every ABI.

Independent tests compare 3,000 Z searches with direct matching, 1,000 multigraph bridge results with edge-removal connectivity, and 700 matrix costs with exhaustive grouping enumeration. Twenty extra assertions check input rejection, maximum declared matrix dimensions, path-depth behavior, cache replacement/eviction, buffer signedness/length and array-copy ownership. Seeds and scope are recorded in java-third-boundaries.json. They are bounded correctness checks, not a load benchmark or proof for unrestricted input.

## Spring additions

Derived Spring Data JPA queries; closed interface projections; fixed-limit identifier keyset pagination; Boot import-resource registration and default-bean back-off; WebFlux SSE mapping/codecs; cancellation propagation; JWT signature/issuer/audience/expiry/scope enforcement; key-matched cache eviction.

The Maven kit passes 59 tests with zero failures, errors or skips, including 17 new tests. Four prior standalone mains retain exact checked outputs. Packaging still selects ReceiptApplication explicitly. The new fixtures are mostly outside that HTTP application's component scan. The Boot label configuration is deliberately included through its import resource; it is not an exposed business endpoint or a separately published starter.

Repository tests use isolated create-drop H2 data. They verify predicates/order, a closed projection with one statement and zero full entity loads, and cursor pages [1,2], [3], []. That is not evidence of a production query plan, large-data performance, snapshot exports or every relationship/projection shape.

The stream test initially found a raw interval publisher overflow under slower downstream demand. The final controller uses a finite range with delayed elements. Mock WebTestClient checks request validation, ordered event encoding, completion and cancellation; it does not start a network server or test reverse-proxy buffering, reconnect replay, deployment capacity or TCP disconnect timing.

JWT tests generate temporary RSA keys locally and exercise the configured security filter chain. A trusted token with read scope returns 200; a valid token with the wrong scope returns 403; missing, expired, wrong-issuer, wrong-audience and untrusted-signature inputs return 401. No remote authorization server, JWKS rotation, OIDC login, production user store or receipt-specific tenant authorization is supplied.

The cache test checks two tenant keys and evicts only the updated key. Its local cache and backing map have no expiry/capacity or distributed consistency guarantee. The existing API still uses its in-memory ReceiptStore and labelled local fixture identity. The new persistence and security teaching fixtures do not make that API durable or production-authenticated.

## Research and originality

The requested references were opened in order: [Oracle LinkedList](https://docs.oracle.com/javase/8/docs/api/java/util/LinkedList.html), [GeeksforGeeks Java curriculum](https://www.geeksforgeeks.org/java/java/), [W3Schools LinkedList](https://www.w3schools.com/java/java_linkedlist.asp), [BeginnersBook LinkedList](https://beginnersbook.com/2013/12/linkedlist-in-java-with-example/), [CodingNomads linked lists](https://codingnomads.com/java-301-linked-lists). Their text, diagrams and examples were not copied by changing names or values.

Primary contract references: [Linker](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/foreign/Linker.html), [Flow](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Flow.html), [LinkedHashMap](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/LinkedHashMap.html), [NavigableMap](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/NavigableMap.html), [ByteBuffer](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/nio/ByteBuffer.html), [CRC32](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/zip/CRC32.html), [MessageFormat](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/text/MessageFormat.html), [CountDownLatch](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CountDownLatch.html).

Algorithm checks: [CMU Z search lecture](https://www.cs.cmu.edu/~ckingsf/bioinfo-lectures/zalg.pdf), [Princeton undirected graph contracts](https://algs4.cs.princeton.edu/41graph/), [Columbia matrix-chain lecture](https://www.columbia.edu/~cs2035/courses/csor4231.F15/matrix-chain.pdf). Our graph example explicitly supports parallel edges; it does not adopt the no-parallel-edge assumption of the reference bridge implementation.

Spring contract references: [Repository query methods](https://docs.spring.io/spring-data/jpa/reference/repositories/query-methods-details.html), [Projections](https://docs.spring.io/spring-data/jpa/reference/repositories/projections.html), [Boot auto-configuration registration](https://docs.spring.io/spring-boot/reference/features/developing-auto-configuration.html), [WebFlux controller return types](https://docs.spring.io/spring-framework/reference/web/webflux/controller/ann-methods/return-types.html), [WebTestClient](https://docs.spring.io/spring-framework/reference/testing/webtestclient.html), [JWT resource server](https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/jwt.html), [Cache annotations](https://docs.spring.io/spring-framework/reference/integration/cache/annotations.html). Current reference documentation can describe a newer version; executable assertions use the kit's pinned Boot 4.0.8 managed libraries.

Public bodies remain original semantic HTML with internal links and about 6,938 new prose words, excluding source/output. They contain no tables, copied images, marketing claims or AI-detection promises. API facts, standard algorithms, syntax, logos and dependency licences do not become exclusive AI Trove property. The ZIPs contain original source and dependency declarations, excluding downloaded libraries, JDKs, compiled targets and private configuration.

## Current checks and remaining scope

Body links: 1,216, with zero missing/unpublished targets; 65 Java-to-Spring and 111 Spring-to-Java links. Source archives contain 234 Java files and 39 Spring files. Browser checks cover 70 article/hub/quiz screens, shared mobile widths 320/390/768, all 36 Spring answers and the preserved 16-card homepage. All 20 new articles also pass Contents and overflow checks at both 320 and 390 pixels (40 additional screens). No page errors were observed. TypeScript passes.

The coverage map identifies the remaining work: wider native ABI and desktop/Jakarta APIs, further algorithms and adversarial inputs, separately packaged starters and version migrations, target-database/container/recovery tests, real-network streaming, OAuth2/OIDC/JWKS rotation and resource-specific permissions, bounded/distributed caches, durable messaging/outbox and application persistence. Hosted judging, authenticated progress, WordPress import/setup, purchased domain/DNS, launch origin and editorial deployment checks remain separate work. No main merge, live deployment or CMS import occurs in this pass.

Machine-readable evidence: java-program-check.json, spring-content-validation.json, java-third-boundaries.json, third-links-check.json, browser-check.json, new-mobile-check.json and publish-runtime-check.json. The launch-mode build/runtime results are appended after final verification; the development preview stays noindex.

Final build/runtime verification passed. The launch-mode sitemap contains all 310 eligible URLs: 250 Java, 58 Spring, editorial profile and homepage. Seventy checked responses have their canonical tags and structured data in returned HTML. Downloads and coverage utilities retain noindex/nosniff. The selected mobile subject tab is fully visible. Measured Maven libraries include Framework/WebFlux 7.0.9, Spring Data JPA 4.0.7, Spring Security 7.0.7, Hibernate 7.2.24.Final and Reactor 3.8.7. Targeted browser-script lint and whitespace checks pass. The dev preview is restarted in its default noindex mode after the temporary launch-mode build check.
