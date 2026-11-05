# Spring wiring, MVC binding and JDBC batch — 1 October 2026

Six original Spring tutorials were added to the separate Spring & Spring Boot umbrella: primary/qualifier selection, configuration bean-method proxying, ordered collection injection, @ModelAttribute allowlisting, named JDBC list parameters under a tenant predicate, and generated JDBC insert keys. Each has four related internal lesson links plus contextual links in the body. Six earlier lessons link back to this batch, and the relevant Spring Core, Web APIs and Data & Transactions section hubs list the new pages.

Two new JUnit classes in the downloadable Spring source kit check the six behavior claims against the pinned Spring Boot 4.0.8 / Spring Framework 7 dependencies and H2 fixture. The snippets in the public pages are excerpts from those checked classes. The public tutorial bodies contain no external sources or copied examples.

## Research record

The user's five preferred URLs cover Java and LinkedList, not Spring. They remain useful background for Java interlinking but cannot establish Spring's bean, MVC or JDBC contracts. The official Spring documentation was consulted for those contracts:

- https://docs.spring.io/spring-framework/reference/core/beans/introduction.html
- https://docs.spring.io/spring-framework/reference/core/beans/annotation-config/autowired-primary.html
- https://docs.spring.io/spring-framework/reference/core/beans/java/configuration-annotation.html
- https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/context/annotation/Configuration.html
- https://docs.spring.io/spring-framework/reference/core/beans/annotation-config/autowired.html
- https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-data-binding.html
- https://docs.spring.io/spring-framework/reference/data-access/jdbc/core.html
- https://docs.spring.io/spring-boot/reference/index.html

The lessons explain established framework behavior in new receipt and dispatch scenarios. AITrove can own its original prose, tests and scenarios; framework facts and API syntax remain non-exclusive.

## Verification and limits

`mvn -o -q -Dtest=WiringAndBindingContractTest,JdbcParametersAndKeysContractTest test` passes all six new tests. The first full-suite run had socket-binding errors in three existing HTTP test classes because the sandbox initially denied local listening sockets. After enabling network permission for the turn, `mvn -o -q test` passed: 150 tests, zero failures, zero errors and zero skipped cases. The six new tests use in-process contexts, standalone MockMvc and H2; they do not establish target-database, deployed security-filter or live gateway behavior.

Spring is not complete in a universal sense. The existing curriculum has broad local coverage, but Spring Cloud, messaging brokers, R2DBC, GraphQL, Spring AI, multi-node and target-database integration remain substantial separate tracks. Production use also needs human editorial review and tests against the selected release and infrastructure. The Spring source kit is educational, not a deployed service.
