# Java text matching boundaries — editorial handoff

Seven original Java 8 tutorials were added in the Java Tutorial module, "Text matching boundaries." Each contains a complete program, checked output, cost notes, Common Mistakes, and internal lesson links. Four existing string and Unicode lessons link into the new module.

New `/java/` paths: `regex-quote-user-input`, `regex-quote-replacement`, `regex-matches-find`, `regex-find-cursor`, `regex-group-state`, `regex-unicode-flags`, and `regex-split-limit`.

The five user-prioritized Java and LinkedList pages were checked for curriculum context. The API contracts in this batch were checked against:

- https://docs.oracle.com/javase/8/docs/api/java/util/regex/Pattern.html
- https://docs.oracle.com/javase/8/docs/api/java/util/regex/Matcher.html
- https://docs.oracle.com/javase/8/docs/api/java/lang/String.html

The public lesson bodies contain no external URLs or copied examples. The local checker compiles each program for Java 8, compares its output, validates the module and all internal link targets, checks allowed semantic tags, and scans the new bodies for the prohibited terms. These tests do not establish a measured AI-detector score or exclusive ownership of Java API behavior.

Further work: hostile-input performance tests for each production regex, a real import parser with quoting and escape rules, Unicode normalization policies tied to storage, and tests against the JDKs actually used by readers.
