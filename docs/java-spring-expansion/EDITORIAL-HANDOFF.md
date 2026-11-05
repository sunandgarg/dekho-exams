# Current continuation

The latest pass adds twelve Java and eight Spring articles: Java now has 226 articles, 10 hubs and 14 quizzes; separate Spring & Spring Boot has 45 articles, 10 hubs and 3 quizzes. Current verification and unfinished scope are in [THIRD-PASS.md](THIRD-PASS.md) and the coverage map. [NEXT-PASS.md](NEXT-PASS.md) preserves the d391616 snapshot. The older expansion below records 3605a18; its counts are historical.

# Java and separate Spring subject: editorial handoff

This pass adds 11 Java lessons and 29 Spring lessons. Spring & Spring Boot has ten independent section hubs and three twelve-question banks. Java module lists contain no Spring routes; 32 new Java-to-Spring body links connect the contracts. Spring bodies contain 288 deliberate internal links, including section and prerequisite links.

Java now has 206 articles, ten hubs and fourteen quizzes: 230 routes. Spring has 29 articles, ten hubs and three quizzes: 42 routes. The full two-subject export contains 272 records; the reviewed export includes the editorial profile for 273 records. The launch sitemap adds the homepage, producing 274 eligible URLs when the preview gate is explicitly disabled. These are populated curricula, not exhaustive language/framework coverage or a ranking guarantee.

The writing, receipt application, teaching programs and questions are newly written for AI Trove. Research checks facts and coverage; examples are not made by changing values in someone else’s program. Java/Spring APIs, technical facts, trademarks and declared third-party dependencies retain their own ownership and licences. Public tutorial bodies use semantic HTML and internal links; research URLs are recorded here rather than inserted into those bodies.

## Java additions

Clock injection and exact expiry; daylight-saving gaps/overlaps; eager Optional defaults; Spliterator partitions and characteristics; collector key collisions; stream close ownership; ThreadLocal cleanup; bounded executor admission; SecureRandom token encoding; iterative segment-tree sums; minimum coin change with unreachable states. Each has a complete compiled program, checked output, costs, rejected-input boundaries and Common Mistakes.

Verification compiles 195 distinct Java programs/fragments and executes 184, checking 169 declared outputs against releases 8, 11, 17, 21 and 25. Existing dependency-specific JDBC/JUnit/JMH checks remain recorded in the earlier release; this pass does not relabel every dependency program as a standalone JDK test. The two new algorithms pass 40,500 comparisons against independent direct-sum and BFS oracles.

## Spring scope and evidence

Pinned learning baseline: JDK 21, Maven, Spring Boot 4.0.8 with its managed Framework 7 dependencies. This version is a reproducible baseline, not a claim to be the latest release. The source kit declares starter-webmvc, validation, JDBC, security, actuator and test dependencies. No dependency binaries, private environment files, toolchains or compiled targets are distributed.

Thirty passing Maven tests check direct construction, singleton/prototype identity, qualifiers, cleanup, local events, proxy self-invocation, configuration conversion/validation, environment selection, conditional assembly, tenant cache ownership, MVC input/errors, page limits/snapshots, H2 rollback/constraints, real HTTP health/authentication/CORS and CSRF boundaries. Four standalone teaching mains also have exact checked outputs. Packaging selects ReceiptApplication explicitly.

The receipt API uses an in-memory store. The JDBC transaction fixture is separate; it is not the API repository. Fixture Basic credentials are clearly labelled in code and README and are unsuitable for deployment. CSRF stays enabled. A Basic header with no token is rejected before authentication in the checked request path (401); an established user with no token receives 403; an established user with a valid token can create the valid receipt. These are distinct checked behaviors.

MockMvc standalone tests do not claim complete security coverage; filter-chain tests use the web context and security integration. Local H2 checks do not prove target-database isolation. A local cache has no distributed invalidation or expiry policy; a local event is not a durable broker. Async tasks have bounded admission and no persistence claim. The source-kit ZIP is a learning artifact, not the website’s deployed backend.

## Research order and sources

The requested sites were inspected in this order for contracts and curriculum coverage. Technical claims are verified against primary documentation; explanations and examples are original.

1. [Oracle 8 LinkedList](https://docs.oracle.com/javase/8/docs/api/java/util/LinkedList.html)
2. [GeeksforGeeks Java curriculum](https://www.geeksforgeeks.org/java/java/)
3. [W3Schools LinkedList](https://www.w3schools.com/java/java_linkedlist.asp)
4. [BeginnersBook LinkedList](https://beginnersbook.com/2013/12/linkedlist-in-java-with-example/)
5. [CodingNomads linked lists](https://codingnomads.com/java-301-linked-lists)

Additional primary references:

- [Clock](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/time/Clock.html), [ZoneRules](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/time/zone/ZoneRules.html), [Optional](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/Optional.html), [Spliterator](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/Spliterator.html), [Collectors](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/stream/Collectors.html), [BaseStream](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/stream/BaseStream.html), [ThreadPoolExecutor](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html), [ThreadLocal](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/ThreadLocal.html), [SecureRandom](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/security/SecureRandom.html).
- [Boot 4.0 requirements](https://docs.spring.io/spring-boot/4.0/system-requirements.html), [dependency injection](https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html), [bean scopes](https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html), [lifecycle](https://docs.spring.io/spring-framework/reference/core/beans/factory-nature.html), [context events](https://docs.spring.io/spring-framework/reference/core/beans/context-introduction.html), [proxy dispatch](https://docs.spring.io/spring-framework/reference/core/aop/proxying.html).
- [Boot auto-configuration](https://docs.spring.io/spring-boot/4.0/reference/using/auto-configuration.html), [external configuration](https://docs.spring.io/spring-boot/4.0/reference/features/external-config.html), [profiles](https://docs.spring.io/spring-boot/4.0/reference/features/profiles.html), [MVC validation](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-validation.html), [ProblemDetail](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-ann-rest-exceptions.html), [CORS](https://docs.spring.io/spring-framework/reference/web/webmvc-cors.html).
- [JDBC core](https://docs.spring.io/spring-framework/reference/data-access/jdbc/core.html), [programmatic transactions](https://docs.spring.io/spring-framework/reference/data-access/transaction/programmatic.html), [transaction advice](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html), [request authorization](https://docs.spring.io/spring-security/reference/servlet/authorization/authorize-http-requests.html), [CSRF](https://docs.spring.io/spring-security/reference/servlet/exploits/csrf.html), [password storage](https://docs.spring.io/spring-security/reference/features/authentication/password-storage.html).
- [MockMvc](https://docs.spring.io/spring-framework/reference/testing/mockmvc/overview.html), [Actuator endpoints](https://docs.spring.io/spring-boot/4.0/reference/actuator/endpoints.html), [task execution](https://docs.spring.io/spring-framework/reference/integration/scheduling.html), [cache advice](https://docs.spring.io/spring-framework/reference/integration/cache/annotations.html).

Research does not amount to an exhaustive crawl of the internet. Full remaining scope is in COVERAGE-AND-REMAINING.md and the interactive learning map. Spring Data JPA, WebFlux, OAuth2/OIDC, distributed messaging, production recovery and further native/desktop Java tracks remain explicit work, not silently completed labels.

## Configuration and launch

The website remains React 19/TypeScript, TanStack Start/Router/Query, Vite 8, Tailwind 4 and Cloudflare Workers. WordPress with the custom AITrove PHP Content API is the intended editorial CMS. The verified local server uses fixtures; this pass does not install/import WordPress content or change Hostinger.

WORDPRESS_URL supplies the server CMS origin. VITE_SITE_URL supplies the canonical frontend origin. VITE_PREVIEW_MODE defaults to true, emitting noindex and an empty sitemap. New ready entries join the existing metadata-driven sitemap only when the launch gate is disabled. Coverage maps and source downloads stay noindex. Private attempts, cross-device identity, hosted judging and payment features still need backend services.

Local preview: http://127.0.0.1:3001/java/java and http://127.0.0.1:3001/spring/spring-boot. The combined map is /learning-coverage.html; /java-coverage.html starts with the Java filter. The approved sixteen homepage topic cards remain, with a compact separate framework link beneath them.

## Final site checks

The built Cloudflare runtime returns the expected 274-URL launch sitemap (230 Java, 42 Spring, editorial profile and homepage). All 53 added article/hub/quiz routes pass status, canonical and structured-data checks. Downloads and maps remain noindex/nosniff. The restored development preview stays noindex with an empty sitemap. Browser checks cover 320, 390, 768 and 1440-pixel viewports, module navigation, mobile Contents, all 36 Spring quiz answers, both downloads and the preserved sixteen-card homepage. Long test identifiers now wrap within article prose, and the selected subject is kept fully visible in the horizontal topic bar without moving page scroll.

Production build and TypeScript checks pass. Targeted ESLint reports zero errors and one existing Fast Refresh export warning in templates.tsx. Browser checks report no page errors. Source ZIP validation excludes compiled targets and private configuration. Verification JSON files in this directory retain the measured counts and limits.
