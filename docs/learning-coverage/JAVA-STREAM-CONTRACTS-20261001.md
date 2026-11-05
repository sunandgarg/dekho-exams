# Java Stream and collector contract batch — 1 October 2026

This batch adds eight original, Java 8-compatible lessons to the Java hub. It covers a single-use stream, `peek` side effects, duplicate keys in `toMap`, null classifiers in `groupingBy`, explicit `LinkedHashMap` ordering, parallel `forEachOrdered`, reduction identities, and short-circuit `anyMatch`. Six existing lessons link back into the batch. Each new article has five or six contextual internal links and an executable example with a checked output.

## Research boundary

The user's preferred sources were reviewed in order for catalog context. Oracle's Java 8 LinkedList API remains the primary reference for the earlier LinkedList cluster. The GeeksforGeeks Java hub shows breadth of curriculum, while W3Schools, Beginnersbook and Coding Nomads are beginner-level LinkedList treatments. These pages did not provide the authoritative behavioral contracts for this Stream batch. Those contracts were checked against the official Java 8 API pages for Stream, Collectors and Optional:

- https://docs.oracle.com/javase/8/docs/api/java/util/LinkedList.html
- https://www.geeksforgeeks.org/java/java/
- https://www.w3schools.com/java/java_linkedlist.asp
- https://beginnersbook.com/2013/12/linkedlist-in-java-with-example/
- https://codingnomads.com/java-301-linked-lists
- https://docs.oracle.com/javase/8/docs/api/java/util/stream/Stream.html
- https://docs.oracle.com/javase/8/docs/api/java/util/stream/Collectors.html
- https://docs.oracle.com/javase/8/docs/api/java/util/Optional.html

The public lesson bodies contain no external URLs and do not copy the source examples. They use newly authored invoice, shipment, receipt and warehouse scenarios. The external API pages establish language/library behavior; they do not make AITrove the sole proprietor of those facts.

## Checks

`python3 work/check-java-stream-contracts.py` compiles each Java block with `javac --release 8`, then runs it five times on JDK 25 and five times on the system JDK. It also checks allowed HTML, the Common Mistakes section, internal link targets, related-page references, banned wording and output. TypeScript, ESLint and the Pages build are separate deployment checks.

## Open work

The Java catalog is extensive but cannot be declared complete against the whole platform and ecosystem. Useful next clusters include primitive stream specialization and boxing cost, collector downstream composition, safe file-stream processing, `Spliterator` characteristics, `CompletableFuture` composition, JVM observability, and more Java version-specific migration guidance. Java 8 API behavior must not be presented as the whole of current Java. Newly added pages also need human editorial review and production analytics before any ranking or learning-outcome claim.
