# Spring foundations editorial handoff

This pass adds six original Spring lessons in the existing Spring & Spring Boot subject: component registration, circular constructor dependencies, the MVC request path, filters versus interceptors, authorization matcher order, and CSRF for browser sessions. Java language content stays under `/java/`. Each new lesson is in a Spring curriculum module, links to relevant existing lessons, and has an original Java listing compiled against the project's Spring source-kit classpath.

The Java LinkedList and third-party tutorial URLs in the brief cover a different subject. They were not used as Spring implementation sources. Technical claims for this pass were checked against the Spring project's primary documentation:

- [Spring IoC container](https://docs.spring.io/spring-framework/reference/core/beans.html) and [dependency injection and circular references](https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html)
- [Component scanning and stereotypes](https://docs.spring.io/spring-framework/reference/core/beans/classpath-scanning.html)
- [DispatcherServlet processing](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-servlet/sequence.html), [Servlet filters](https://docs.spring.io/spring-framework/reference/web/webmvc/filters.html), and [MVC interceptors](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-config/interceptors.html)
- [Spring Security request authorization](https://docs.spring.io/spring-security/reference/7.0/servlet/authorization/authorize-http-requests.html) and [CSRF protection](https://docs.spring.io/spring-security/reference/7.0/servlet/exploits/csrf.html)

Examples are teaching listings, not a claim that every surrounding deployment has been tested. The compile check proves syntax and dependency compatibility for these listings. It does not run HTTP, browser, database or deployment behavior. The broader Spring source kit supplies separate tests for existing lessons.

Further content still needs dedicated work: OAuth2 login/client flows, production connection-pool sizing with a real database, trace propagation across async work, Spring Batch, WebSocket messaging, messaging brokers, and version-specific migration guides. Each should be built with runnable fixtures and explicit failure tests before being marked verified.
