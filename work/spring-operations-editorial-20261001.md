# Spring operations batch — editorial handoff

Added 12 original lessons: Gateway circuit-breaker fallback and route refresh access; Redis Cluster key slots and cache outage policy; STOMP relay availability and reconnect state recovery; HTTP service groups, WebClient response ownership and reactive proxy calls; Testcontainers migration ownership and parallel data isolation; OAuth2 client token scope. Tutorial bodies contain only deliberate internal lesson links and no research URLs. The requested Java LinkedList reading list is not relevant to these Spring contracts, so it was not used as a prose or outline source.

Official API and behavior checks:

- Gateway breaker and fallback: https://docs.spring.io/spring-cloud-gateway/reference/spring-cloud-gateway-server-webflux/gatewayfilter-factories/circuitbreaker-filter-factory.html
- Gateway actuator route refresh and access: https://docs.spring.io/spring-cloud-gateway/reference/spring-cloud-gateway-server-webflux/actuator-api.html
- Spring Data Redis Cluster: https://docs.spring.io/spring-data/redis/reference/redis/cluster.html
- STOMP broker relay configuration and availability: https://docs.spring.io/spring-framework/reference/web/websocket/stomp/handle-broker-relay-configure.html
- HTTP service groups: https://docs.spring.io/spring-framework/reference/integration/rest-clients.html
- WebClient exchange ownership: https://docs.spring.io/spring-framework/reference/web/webflux-webclient/client-exchange.html
- Spring Boot Testcontainers: https://docs.spring.io/spring-boot/reference/testing/testcontainers.html
- OAuth2 authorized clients: https://docs.spring.io/spring-security/reference/servlet/oauth2/client/authorized-clients.html and https://docs.spring.io/spring-security/reference/reactive/oauth2/client/authorized-clients.html

The examples are implementation sketches. No new Spring application, Redis Cluster, Gateway fleet, STOMP broker, OAuth2 authorization server, or database container was provisioned for this batch. Existing Spring kit tests do not execute these new examples. Remaining high-value work: executable integration suites for each operational boundary, broker failover drills, Gateway route-control authorization checks, HTTP client timeout and cancellation tests, Redis Cluster resharding tests, and compatibility review against the exact deployed framework versions. The Spring ecosystem remains open-ended; article count is not a claim of full coverage.
