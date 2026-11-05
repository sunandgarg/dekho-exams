# Spring GraphQL and R2DBC editorial handoff

The five user-priority links in this request cover Java and LinkedList, not Spring GraphQL or R2DBC. They were not used as technical authority for this expansion. Public tutorial bodies contain original prose and no external source links.

Contract checks used these primary references:

- Spring GraphQL 2.0.5 request execution and GraphQlSource: https://docs.spring.io/spring-graphql/reference/request-execution.html
- Spring GraphQL controller and field-mapping model: https://docs.spring.io/spring-graphql/reference/controllers.html
- Spring GraphQL test layers: https://docs.spring.io/spring-graphql/reference/testing.html
- Spring Framework R2DBC DatabaseClient and binding: https://docs.spring.io/spring-framework/reference/data-access/r2dbc.html
- Spring Boot R2DBC configuration and JDBC back-off: https://docs.spring.io/spring-boot/reference/data/sql.html
- Spring Data R2DBC overview: https://docs.spring.io/spring-data/relational/reference/r2dbc.html

The pinned source kit is Boot 4.0.8 with Spring GraphQL 2.0.5. Direct GraphQlSource tests do not expose an HTTP endpoint or authenticate a tenant. The nested reactive-r2dbc project uses Boot-managed H2 2.4.240 and r2dbc-h2 1.1.0.RELEASE. The original JDBC project retains H2 2.3.232; an attempted shared test classpath produced NoSuchMethodError in r2dbc-h2 before SQL execution. The projects remain isolated and should be run independently.

Remaining checks before production claims: actual GraphQL Boot registration, HTTP authentication/context propagation, nested field authorization, query depth and cost policy, error sanitization, target-database R2DBC concurrency, pool saturation, cancellation, and real cross-service delivery. No AI-detector score or exclusive ownership of framework behavior was verified.
