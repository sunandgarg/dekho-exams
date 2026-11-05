# Java asynchronous contracts packet

Added eight standalone Java lessons and one eight-question quiz. The lessons cover dependent composition, independent combination, two-stage result races, asynchronous recovery, blocking wait semantics, future cancellation, bounded `invokeAll`, and first-success `invokeAny`. They are discoverable from the Java root and advanced-Java modules, connect to each other, and have backlinks from relevant older lessons.

The public article bodies use original examples, semantic HTML, explicit failure cases, cost and ownership discussion, and a Common Mistakes section. They contain no external source links. Each Java snippet compiles at its declared release; local smoke tests exercise the main contracts. The WordPress import packet contains 489 records, all marked draft. This repository does not publish those records to WordPress.

Validation: `python3 scripts/check-java-async-contracts.py`; `python3 scripts/export-java-for-wordpress.py`; `npm run build`; `npm run lint`; `git diff --check`; and a check that all Java-body internal links resolve. Lint has nine existing warnings and no errors. The build has an existing large-bundle advisory.

Live network services, replica behavior, and interruptibility of external I/O still require integration tests against the chosen clients and infrastructure. The repository-wide Java checker remains unable to bind a local server socket in this sandbox at its existing socket lesson; the new focused checker does not depend on a socket.
