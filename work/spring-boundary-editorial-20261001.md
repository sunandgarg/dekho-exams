# Spring persistence, security and proxy boundary editorial handoff

This file is a private research and verification record. Public tutorial bodies contain no outside citations or copied prose. The ten examples are AITrove scenarios and are labelled implementation sketches; they were not compiled as new source-kit tests in this pass.

Official references checked on 1 October 2026:

- Spring Data JPA query methods, including `@Modifying`, derived deletes, bulk deletes and lifecycle behavior: https://docs.spring.io/spring-data/jpa/reference/jpa/query-methods.html
- Spring Data JPA `@Modifying` API flags: https://docs.spring.io/spring-data/jpa/docs/current/api/org/springframework/data/jpa/repository/Modifying.html
- Spring Data JPA lock metadata: https://docs.spring.io/spring-data/jpa/reference/jpa/locking.html
- Spring Framework annotation-driven transactions, proxy calls and imperative versus reactive transaction contexts: https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html
- Spring Framework propagation and REQUIRES_NEW connection budgeting: https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/tx-propagation.html
- Spring Security resource-server JWT issuer, audience and key validation: https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/jwt.html
- Spring Security session management and session fixation: https://docs.spring.io/spring-security/reference/servlet/authentication/session-management.html
- Spring Security servlet filter architecture and exception translation: https://docs.spring.io/spring-security/reference/servlet/architecture.html
- Spring Framework ForwardedHeaderFilter trust requirements: https://docs.spring.io/spring-framework/reference/web/webmvc/filters.html

The five user-prioritized links are Java and LinkedList material. They were considered for research priority, but they do not specify Spring persistence, security or proxy behavior; official Spring documentation was therefore used for this Spring pass.

Open verification work: compile each sketch against the site's exact Spring Boot/Security dependencies; add application-level JPA tests against the target database, connection-pool saturation tests, real-proxy forwarded-header tests, and browser session rotation tests. Existing source-kit suites still run, but their pass does not verify these ten new sketches.
