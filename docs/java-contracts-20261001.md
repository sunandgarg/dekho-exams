# Java contract expansion — editorial handoff

Eight original tutorials were added to the Java curriculum. They cover an aliased `LinkedList.addAll` source, mutable `HashMap` keys, `BigDecimal` value versus scale equality, trailing fields in `String.split`, admission for `ConcurrentLinkedQueue`, the failure boundary of `BlockingQueue.drainTo`, `CompletableFuture.orTimeout` versus worker cancellation, and atomic file publication with `Files.move`.

The provided LinkedList references were reviewed in the requested order. Oracle's Java 8 API defines the contracts used here; the remaining tutorials informed topic inventory only. The article outlines, prose, programs, values, and outputs were written for AITrove and are not copied examples. Technical facts, Java API names, and standard-library behavior are not exclusive property.

Verification references for editorial review (not embedded in public tutorial bodies):

- Oracle Java 8 LinkedList: https://docs.oracle.com/javase/8/docs/api/java/util/LinkedList.html
- GeeksforGeeks Java overview: https://www.geeksforgeeks.org/java/java/
- W3Schools LinkedList: https://www.w3schools.com/java/java_linkedlist.asp
- BeginnersBook LinkedList: https://beginnersbook.com/2013/12/linkedlist-in-java-with-example/
- CodingNomads linked lists: https://codingnomads.com/java-301-linked-lists
- Oracle Java 8 List and Map contracts: https://docs.oracle.com/javase/8/docs/api/java/util/List.html and https://docs.oracle.com/javase/8/docs/api/java/util/Map.html
- Oracle Java 8 BigDecimal and String contracts: https://docs.oracle.com/javase/8/docs/api/java/math/BigDecimal.html and https://docs.oracle.com/javase/8/docs/api/java/lang/String.html
- Oracle Java 8 ConcurrentLinkedQueue and BlockingQueue contracts: https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/ConcurrentLinkedQueue.html and https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/BlockingQueue.html
- Oracle Java 21 CompletableFuture timeout contract: https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CompletableFuture.html
- Oracle Java 8 Files.move contract: https://docs.oracle.com/javase/8/docs/api/java/nio/file/Files.html

The `Files.move` example does not promise a portable overwrite or power-loss durability. Its output varies if the local filesystem does not support atomic moves, so the content checker compiles and executes it without asserting one platform-specific output string. The timeout fixture uses latches to make the worker outcome reproducible, but its deadline should still be checked on other supported JDKs.

Further editorial work remains open-ended. The next valuable Java gaps are bounded parsing for structured input, production-grade worker shutdown, TLS and HTTP failure handling against real endpoints, and database behavior against specific engines. Do not call the entire language complete based on page count.
