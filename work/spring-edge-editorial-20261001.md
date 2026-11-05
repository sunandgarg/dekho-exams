# Spring edge and cache batch — editorial handoff

This batch adds 12 original Spring articles: Redis cache expiry, key schema and writer races; Gateway filter order, rate limiting and retry/body budgets; STOMP identity, slow-client limits and broker scale; HTTP service-client contract and retry uncertainty; and Testcontainers service-connection lifecycle. Tutorial bodies contain only internal lesson links. The Java LinkedList pages supplied as preferred reading are unrelated to these Spring contracts, so they were not used as structural or prose templates.

Contract checks used for the facts and API sketches:

- Spring Data Redis cache behavior: https://docs.spring.io/spring-data/redis/reference/redis/redis-cache.html
- Spring Cloud Gateway filters and rate limiting: https://docs.spring.io/spring-cloud-gateway/reference/spring-cloud-gateway-server-webflux/global-filters.html and https://docs.spring.io/spring-cloud-gateway/reference/spring-cloud-gateway-server-webflux/gatewayfilter-factories/requestratelimiter-factory.html
- Spring Cloud Gateway retry: https://docs.spring.io/spring-cloud-gateway/reference/spring-cloud-gateway-server-webflux/gatewayfilter-factories/retry-factory.html
- Spring WebSocket STOMP authentication, authorization and transport limits: https://docs.spring.io/spring-framework/reference/web/websocket/stomp/authentication.html , https://docs.spring.io/spring-security/reference/7.0/servlet/integrations/websocket.html , https://docs.spring.io/spring-framework/reference/web/websocket/stomp/configuration-performance.html
- Spring HTTP service clients: https://docs.spring.io/spring-framework/reference/integration/rest-clients.html
- Spring Boot Testcontainers: https://docs.spring.io/spring-boot/reference/testing/testcontainers.html

The examples are deliberately marked as implementation sketches. No new example in this batch has been compiled against a Spring application or load-tested against Redis, Gateway, a STOMP broker, or a live database container. The existing Spring kit tests validate earlier lessons, not these 12 runtime configurations.

Remaining work after this batch: integration tests for the new examples; Spring Data Redis serializer migrations and cluster failover; Gateway circuit-breaker/fallback and route reload behavior; WebSocket broker relay credentials and reconnect delivery; HTTP service groups and reactive client variants; Testcontainers multi-database migrations and CI parallelism; ongoing framework-version review. No finite article count can establish that the entire Spring ecosystem is “fully” covered.
