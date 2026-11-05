# Java list adapters and mutation boundaries — editorial handoff

Eight original Java 8 tutorials were added to the Java Tutorial module, "List adapters and mutation boundaries." They cover synchronized iteration, removal overloads, partial replaceAll failure, Collections.copy destination size, rotation through a subList view, a LIFO queue adapter, nCopies reference aliasing, and LinkedList spliterator binding. Each has a runnable program, verified output, practical cost and failure notes, Common Mistakes, and internal links. Five existing lessons link back into the module.

New `/java/` paths: `linkedlist-synchronized-iteration`, `linkedlist-remove-overload`, `list-replaceall-partial-failure`, `collections-copy-destination-size`, `collections-rotate-sublist`, `collections-lifo-queue-deque`, `collections-ncopies-alias`, and `linkedlist-spliterator-binding`.

The user-prioritized pages were checked for topic coverage, not copied. API behavior was checked against:

- https://docs.oracle.com/javase/8/docs/api/java/util/LinkedList.html
- https://www.geeksforgeeks.org/java/java/
- https://www.w3schools.com/java/java_linkedlist.asp
- https://beginnersbook.com/2013/12/linkedlist-in-java-with-example/
- https://codingnomads.com/java-301-linked-lists
- https://docs.oracle.com/javase/8/docs/api/java/util/Collections.html
- https://docs.oracle.com/javase/8/docs/api/java/util/List.html
- https://docs.oracle.com/javase/8/docs/api/java/util/Arrays.html
- https://docs.oracle.com/javase/8/docs/api/java/util/Spliterator.html

No external URLs appear in the public lesson bodies. The local checker compiles every program at the Java 8 source level, compares output, checks internal link targets and the navigation module, restricts tutorial-body tags, and scans for the prohibited terms. The checked outputs describe the local fixture; they do not establish behavior under all concurrent schedules. No AI-detector score was measured, and Java API contracts are not exclusive property.

Remaining work: high-contention tests for actual application workloads, ownership tests for mutable element graphs, collection adapters used with persistence boundaries, and a multi-JDK run matrix.
