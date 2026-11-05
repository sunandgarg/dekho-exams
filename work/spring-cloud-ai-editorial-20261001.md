# Spring Cloud and Spring AI editorial handoff — 2026-10-01

This file records research used to check API behavior and scope. It is not a public lesson or a claim of human authorship. The 13 public lessons are newly written boundary explanations and design sketches; a 14-question browser self-check tests the stated decisions. The current source kit does not include Spring Cloud or Spring AI dependencies; none of their snippets is represented as an executed integration test.

The five URLs supplied as research priorities cover Java and `LinkedList`, not Spring Cloud or Spring AI. They were reviewed for relevance and not used to assert Cloud or AI behavior:

1. https://docs.oracle.com/javase/8/docs/api/java/util/LinkedList.html
2. https://www.geeksforgeeks.org/java/java/
3. https://www.w3schools.com/java/java_linkedlist.asp
4. https://beginnersbook.com/2013/12/linkedlist-in-java-with-example/
5. https://codingnomads.com/java-301-linked-lists

Official product documentation checked for this pass:

- https://docs.spring.io/spring-cloud-gateway/reference/ — Gateway 5.0.3 targets Framework 7 / Boot 4 and has separate WebFlux and MVC server variants.
- https://docs.spring.io/spring-cloud-circuitbreaker/reference/ — Circuit Breaker 5.0.3 implementation choices and blocking/reactive distinctions.
- https://docs.spring.io/spring-cloud-config/reference/client.html — `spring.config.import`, required/optional Config Server behavior and profile resolution.
- https://docs.spring.io/spring-cloud-commons/reference/spring-cloud-commons/common-abstractions.html — service selection and retry properties.
- https://docs.spring.io/spring-ai/reference/ — Spring AI 2.0.1 topic map.
- https://docs.spring.io/spring-ai/reference/api/chatclient.html — synchronous and streaming ChatClient paths.
- https://docs.spring.io/spring-ai/reference/api/retrieval-augmented-generation.html — metadata filtering in retrieval.
- https://docs.spring.io/spring-ai/reference/api/tools.html — application-owned tool execution and ToolContext.

Next executable integration work, before claiming deployment-level coverage:

1. Create a separate Spring Cloud Boot 4 project with a selected 2025.1 release-train BOM. Run an unreachable Config Server startup test, a gateway route and trusted-identity test, load-balanced read retry test, and POST timeout-after-commit replay test.
2. Create a separate Spring AI 2.0 project with a fake ChatModel, tenant-filtered test vector store, memory repository and narrow tool. Assert cross-tenant retrieval denial, forged model tool arguments, cancellation, bounded tool loops and output validation. Then repeat provider-specific checks with a configured account.
3. Keep the published source kit's dependency graph unchanged until these projects compile and pass. The existing 174 main and six R2DBC tests do not exercise Cloud or AI.
4. Continue broader Spring coverage: actual GraphQL HTTP/authentication/query-cost wiring, target database tests for R2DBC concurrency and cancellation, broker-backed Kafka delivery, and wider Spring ecosystem modules such as Modulith and Batch.
