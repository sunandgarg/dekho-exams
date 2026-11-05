# Java runtime discovery packet

Eight standalone lessons and one eight-question quiz were added. They cover reflective target exceptions, exact overload lookup, denied deep reflection, proxy Object-method behavior, ServiceLoader provider failure, noninitializing class lookup, module export/open checks, and exact MethodHandle calls. New pages are reachable from the Java root and advanced-Java modules, link to related new and existing lessons, and receive backlinks from older reflection, module, annotation, and VarHandle articles.

Public bodies use semantic HTML, original domain examples, a definition, an operational contract, a failure case, a compile-ready Java snippet, performance and ownership cost, and Common Mistakes. They contain no external reference links. The import packet now contains 498 draft records; the repository is a preview source and does not publish to WordPress.

Validation: `python3 scripts/check-java-reflection-contracts.py` compiled eight snippets at their declared releases and ran local smoke checks. The exporter completed. All Java internal links resolve. `npm run build` passed; `npm run lint` reported no errors and nine existing warnings. `git diff --check` passed.

Provider packaging in a named module, deep reflection across actual module boundaries, and third-party class-loader behavior still require integration tests with a packaged application. The existing repository-wide Java checker stops at an unchanged local socket lesson because this sandbox blocks binding a server socket; the focused checker has no socket dependency.
