# Spring operations editorial handoff

This pass adds seven original tutorials to the existing Spring & Spring Boot subject: OAuth2 browser login, service-token acquisition, batch chunk restart, WebSocket/STOMP messaging, JDBC pool capacity, transaction isolation, and async trace context. The Java LinkedList and general Java tutorial links in the brief concern Java language content; they were not treated as Spring implementation sources. No prose or example was copied from those sites.

Technical claims were checked against these primary references:

- [Spring Security OAuth2 login](https://docs.spring.io/spring-security/reference/7.0/servlet/oauth2/login/core.html) and [OAuth2 client authorization](https://docs.spring.io/spring-security/reference/7.0/servlet/oauth2/client/core.html)
- [Spring Batch chunk configuration](https://docs.spring.io/spring-batch/reference/step/chunk-oriented-processing/configuring.html), [step restart](https://docs.spring.io/spring-batch/reference/step/chunk-oriented-processing/restart.html), and the Spring Batch 6.0.5 API jars resolved by the project's Boot 4.0.8 dependency management
- [STOMP over WebSocket](https://docs.spring.io/spring-framework/reference/web/websocket/stomp.html) and [WebSocket authentication](https://docs.spring.io/spring-framework/reference/web/websocket/stomp/authentication.html)
- [Boot SQL datasource configuration](https://docs.spring.io/spring-boot/reference/data/sql.html), [transaction settings](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html), and [Boot observability](https://docs.spring.io/spring-boot/reference/actuator/observability.html)

All seven Java listings compile against the Spring Boot 4.0.8 managed dependencies, including OAuth2 client, Spring Batch 6.0.5 and Spring WebSocket modules added to the temporary compile classpath for verification. The listings have not been run against an identity provider, external broker, production database or tracing backend. Those integration checks are still required before presenting the examples as deployment recipes.

The Spring curriculum now has 196 articles, 10 section hubs and 9 quizzes. The new articles are in their relevant modules and have links from existing lessons. Further work includes OAuth2 provider integration tests, a real-database concurrency test for isolation and pool pressure, Batch restart under a killed process, WebSocket message authorization with a broker, and distributed trace export across services.
