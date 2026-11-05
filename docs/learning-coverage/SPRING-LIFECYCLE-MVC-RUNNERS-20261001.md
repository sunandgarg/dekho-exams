# Spring lifecycle, MVC dispatch and Boot runners — 1 October 2026

Eight original tutorials were added to the separate Spring & Spring Boot umbrella. Spring Core now links lazy singleton creation, lazy injection-point proxying and @DependsOn initialization/destruction. Web APIs covers MVC query-parameter mapping, controller-local exception handling and scoped controller advice. The Boot hub covers startup runner arguments and failure. Each new page has four declared related routes plus contextual body links, and six established pages link back to this batch.

The downloadable source kit adds LifecycleAndMvcDispatchContractTest with eight local checks. One early assertion exposed an important distinction: a lazy injection-point proxy alone did not stop an otherwise eager bean being constructed at context refresh. The final test marks the target bean lazy and checks construction on first method call. Public prose and the receipt/dispatch examples were written for AITrove; the framework behavior itself is not proprietary.

## Research record

The user's five prioritized links describe Java and LinkedList. They were useful to the earlier Java work but do not define Spring lifecycle, MVC or Boot runner behavior. The checked behavior in this batch was researched against official Spring documentation:

- https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-lazy-init.html
- https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-dependson.html
- https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-requestmapping.html
- https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-exceptionhandler.html
- https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-advice.html
- https://docs.spring.io/spring-boot/reference/features/spring-application.html

The public tutorial bodies include only internal links and contain no source URLs, copied documentation examples or external diagrams. Each article states the behavior its local test proves and the larger production behavior it does not prove.

## Verification and remaining work

The eight new JUnit methods pass with the pinned Spring Boot 4.0.8 / Spring Framework 7 dependencies. The complete source-kit Maven suite passes: 158 tests, zero failures, errors or skipped cases. TypeScript and the Pages build pass; ESLint exits with zero errors and seven pre-existing Fast Refresh warnings. The source kit uses non-web contexts and standalone MockMvc for these additions, so it does not prove load, external identity, broker delivery or target-database behavior.

The Spring curriculum is still not universal coverage. The largest remaining tracks include Spring Cloud, Kafka and other broker integrations, R2DBC, GraphQL, Spring AI, distributed deployment behavior and target-infrastructure tests. Those need distinct dependencies, exercises and integration environments before being called complete.
