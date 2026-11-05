# Java concurrency failure contracts — editorial handoff

Ten original Java 8 tutorials were added to the Advanced Java module, "Concurrency failure contracts." Each has a complete program, verified output, cost and failure notes, Common Mistakes, and internal links. Seven existing concurrency lessons link into this module. The new programs were run ten times each after compilation to check that their displayed output is stable.

New `/java/` paths: `stampedlock-optimistic-read`, `readwritelock-downgrade`, `atomicstampedreference-aba`, `cyclicbarrier-broken-state`, `synchronousqueue-handoff`, `volatile-counter-lost-update`, `concurrenthashmap-compute-contention`, `lock-interruptibly`, `condition-await-loop`, and `uncaught-exception-handler`.

The user's prioritized Java and LinkedList pages were reviewed for curriculum inventory and were not used as source text or code. Primary API checks for this batch:

- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/locks/StampedLock.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/locks/ReentrantReadWriteLock.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/atomic/AtomicStampedReference.html
- https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/CyclicBarrier.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/SynchronousQueue.html
- https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/ConcurrentHashMap.html
- https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/locks/Condition.html
- https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/locks/Lock.html

No external URLs appear in the public lesson bodies. The fixtures establish the stated local contracts. They are not performance benchmarks or proofs against every possible thread interleaving. A later pass should add high-contention stress, interruption storms, time-bounded waits under load, structured task ownership across supported JDK releases, and incident-oriented exercises. Java API facts are not exclusive property, and no AI-detector score is measured here.
