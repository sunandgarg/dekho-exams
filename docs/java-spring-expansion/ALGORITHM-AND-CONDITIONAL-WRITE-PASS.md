# Java algorithms and Spring conditional-write pass — 30 September 2026

The local curriculum now has 264 Java articles across 10 hubs, 14 Java quizzes, and 54 Spring & Spring Boot articles across 10 separate hubs with 3 quizzes. Spring remains an independent subject at `/spring/spring-boot`; it is linked from relevant Java pages, not inserted into the Java module list. There are 702 generated learning routes in the combined Java, Spring and Python export.

Eight Java DSA lessons were added: half-open prefix-sum queries, inclusive difference-array updates, next-greater monotonic stacks, sliding-window maxima, weighted interval scheduling, bipartite matching by augmenting paths, Edmonds-Karp max flow, and A* on a unit-cost grid. Each page defines its input contract, costs and failure cases, and links to existing prerequisites and nearby problems. The sample programs and explanations were written for AI Trove rather than adapted by changing values in another tutorial. The Java content checker compiled 253 programs or fragments, executed 242, and checked 227 declared outputs across releases 8, 11, 17, 21 and 25; it passed all 274 Java pages and 258 internal-link targets. This check is broad, but it is not an independent property test for every new algorithm or a performance benchmark.

One Spring Web API lesson covers an `If-Match` receipt write. The downloadable source kit's `ReceiptIfMatchWriteTest` checks missing preconditions (the fixture's 428 policy), a stale strong tag (412), a successful update, and a repeat stale write that leaves the newer state intact. The full Maven suite passed 68 tests, and the Spring content checker found 54 articles, 484 body links, 110 link targets and zero curriculum orphans. This is one synchronized in-memory controller. Real multi-instance writes require an atomic persistent compare-and-update; authorization, persistence, full validator syntax and proxy behavior are not established by the fixture. The ZIP was rebuilt from the checked source kit.

The user-specified reference pages were inspected in order for contracts and curriculum coverage. None of their prose or examples was inserted into public tutorial bodies:

1. [Oracle Java 8 LinkedList API](https://docs.oracle.com/javase/8/docs/api/java/util/LinkedList.html)
2. [GeeksforGeeks Java overview](https://www.geeksforgeeks.org/java/java/)
3. [W3Schools Java LinkedList](https://www.w3schools.com/java/java_linkedlist.asp)
4. [BeginnersBook LinkedList](https://beginnersbook.com/2013/12/linkedlist-in-java-with-example/)
5. [CodingNomads linked lists](https://codingnomads.com/java-301-linked-lists)

The new Spring HTTP contract was checked against [Spring MVC conditional requests](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-caching.html) and [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html). These are research sources, not endorsements or grants of ownership over APIs, facts, names or third-party dependencies.

The production build and tutorial HTML checks pass. The development preview remains gated from indexing; this pass does not deploy to Cloudflare or import entries into WordPress. The [coverage map](COVERAGE-AND-REMAINING.md) keeps remaining Java, Spring and launch work explicit. In particular, the Java curriculum is not an exhaustive language/API reference; sparse and large adversarial graph workloads, more string problems, system-level boundaries, and independently reviewed explanations remain. Spring still needs durable storage, real identity and tenant enforcement, release/deployment matrices, proxy/load behavior and production recovery checks.
