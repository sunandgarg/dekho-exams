# Spring store and platform editorial handoff — 2026-10-01

Added 12 original AI Trove articles: three each for Cassandra, Neo4j, Spring Cloud Kubernetes, and Spring Security SAML. These are new explanations and application scenarios, not adaptations of source examples. The five Java/LinkedList pages supplied in the request were reviewed for relevance; they do not define Spring-specific contracts, so current official Spring references were used for technical fact checks.

## Fact-check references (internal editorial use)

- Spring Data Cassandra mapping and composite keys: https://docs.spring.io/spring-data/cassandra/reference/object-mapping.html
- Spring Data Cassandra template, paging, TTL and options: https://docs.spring.io/spring-data/cassandra/reference/cassandra/template.html
- Spring Data Neo4j mapping and relationship identity: https://docs.spring.io/spring-data/neo4j/reference/object-mapping/metadata-based-mapping.html
- Spring Data Neo4j client and transaction participation: https://docs.spring.io/spring-data/neo4j/reference/appendix/neo4j-client.html
- Spring Cloud Kubernetes starters: https://docs.spring.io/spring-cloud-kubernetes/reference/getting-started.html
- Spring Cloud Kubernetes Config Data precedence: https://docs.spring.io/spring-cloud-kubernetes/reference/property-source-config.html
- Spring Cloud Kubernetes reload properties: https://docs.spring.io/spring-cloud-kubernetes/reference/appendix.html
- Spring Security SAML overview: https://docs.spring.io/spring-security/reference/servlet/saml2/login/overview.html
- Spring Security SAML response authentication: https://docs.spring.io/spring-security/reference/servlet/saml2/login/authentication.html
- Spring Security SAML metadata: https://docs.spring.io/spring-security/reference/servlet/saml2/metadata.html

## Verification boundary and remaining work

The article examples are design sketches, not compiled end-to-end sample applications. A real Cassandra cluster is still needed to test partition hotspots, TTL/tombstones and paging-token behavior. A Neo4j instance is needed to verify mapped relationship saves, rollback and version conflicts. A Kubernetes namespace with the intended service account is needed to test ConfigMap precedence, reload, permissions and service discovery. A test identity provider is needed to verify SAML metadata, signature rotation, clock windows and attribute mapping. The site-level Spring curriculum check, local Java sample suites, TypeScript check and production build are separate from those integration tests.

Future content can cover Cassandra consistency levels and lightweight transactions, Neo4j causal consistency and query plans, Kubernetes informer/RBAC details and SAML single logout. These are not claimed complete by this batch.
