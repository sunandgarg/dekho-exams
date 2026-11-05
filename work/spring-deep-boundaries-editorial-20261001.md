# Spring deep-boundary editorial handoff — 2026-10-01

This batch adds 12 original lessons and four original scenario quizzes (48 explained questions). It extends the Spring Cassandra, Neo4j, Kubernetes, and SAML clusters without copying source prose or examples. The five supplied Java/LinkedList pages do not establish the Spring-specific behavior covered here, so current official Spring references were used to verify the contracts. No research links appear in public tutorial bodies.

## Internal fact-check references

- Cassandra conditional inserts and options: https://docs.spring.io/spring-data/cassandra/reference/api/java/org/springframework/data/cassandra/core/InsertOptions.InsertOptionsBuilder.html
- Cassandra template, optimistic locking and batch limit: https://docs.spring.io/spring-data/cassandra/reference/cassandra/template.html
- Cassandra repository consistency and paging: https://docs.spring.io/spring-data/cassandra/reference/cassandra/repositories/query-methods.html
- Neo4j custom query mapping and root record shape: https://docs.spring.io/spring-data/neo4j/reference/appendix/custom-queries.html
- Neo4j relationship property mapping: https://docs.spring.io/spring-data/neo4j/reference/object-mapping/metadata-based-mapping.html
- Spring Cloud Kubernetes service-account permissions: https://docs.spring.io/spring-cloud-kubernetes/reference/security-service-accounts.html
- Spring Cloud Kubernetes reload properties: https://docs.spring.io/spring-cloud-kubernetes/reference/appendix.html
- Spring Boot application availability: https://docs.spring.io/spring-boot/reference/features/spring-application.html
- Spring Boot Kubernetes probe endpoints: https://docs.spring.io/spring-boot/reference/actuator/endpoints.html
- Spring Security servlet SAML single logout: https://docs.spring.io/spring-security/reference/servlet/saml2/logout.html
- Spring Security SAML metadata: https://docs.spring.io/spring-security/reference/servlet/saml2/metadata.html

## What remains unverified or uncovered

The code blocks are intentionally scoped implementation sketches. They have not been compiled as complete Cassandra, Neo4j, Kubernetes or SAML applications. The new quiz answers were reviewed against the lesson contracts and fixture validation, but no browser-level click-through was run yet. Integration evidence still needs a Cassandra cluster (conditional races, consistency failures, tombstones), a Neo4j instance (query plans, relationship saves, transactions), a Kubernetes namespace with the production service account (RBAC, watcher filtering, probes), and a test IdP (SAML signed response, rollover, both logout directions). Other Spring ecosystem topics remain open; the library should not be described as exhaustive.
