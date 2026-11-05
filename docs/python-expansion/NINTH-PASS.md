# Python expansion, ninth pass — 30 September 2026

This pass adds twenty original lessons and one twelve-question quiz bank. Python now has 280 articles, fourteen section hubs, 21 quiz banks and 252 explained questions across 315 canonical routes. Each new article starts with a technical definition, names its input and ownership boundary, gives a runnable program and verified output, states costs and failure cases, and links to related lessons. The public tutorial bodies contain no copied prose, diagrams or examples from the research sites. Language behavior, algorithms and third-party APIs remain public facts or their respective owners' property. This work does not claim human authorship, detector evasion or search ranking.

## New material

- Tutorial and data types: two-argument `iter` with a bounded sentinel feeder; `bytearray` snapshots, live views and resize blocking.
- Advanced Python: `asyncio.to_thread` context propagation and its cancellation limit; `cached_property` invalidation; a `gather` sibling that outlives the first failure.
- Interview: `try`/`else`/`finally` execution order; comprehension scope and late-bound closures.
- Exercises: stable merge with a declared tie rule; run-length encoding that preserves separated runs; submitted DAG-order validation.
- Testing: `unittest` subtests and asynchronous fixture cleanup.
- Packaging: entry-point discovery and explicit version acceptance policy.
- Data and web: as-of joins with sorted-key boundaries; finite-value gating; in-memory Flask keyset reads with cursor validation.
- Projects and DSA: a transactional in-memory SQLite checkpoint fixture; Floyd–Warshall all-pairs costs and negative-cycle rejection; max flow with residual edges.
- Quiz: twelve explained questions on these operation and failure contracts.

The new programs are standalone teaching fixtures, not hosted services. Code references to other AITrove pages remain in the lesson HTML rather than executable source, preserving runnable examples. A coverage report lists every page and the unfinished scope: `/learning-coverage.html?subject=Python`.

## What the checks establish

All 280 article programs run in isolated temporary directories on CPython 3.14.6 and match their displayed output. Their syntax parses under the 3.11 grammar; that is not a 3.11 runtime test. The nine Python source-kit test files contain 104 suites and 144,404 bounded oracle comparisons. The ten new suites contribute 6,500 comparisons; they include independent small-case reference checks for stable merge, run grouping, DAG order, all-pairs shortest paths, minimum cuts and finite masks. The extracted ZIP's new test suite runs successfully.

Python lesson bodies now contain 2,351 internal links to 350 distinct targets, and all 3,582 learning-body links across Java, Spring and Python resolve to published fixtures. No Python curriculum page is orphaned. The Python section entry counts are 38 tutorial, 27 data types, 37 advanced, twelve interview, fifteen exercises, 21 examples, 21 quizzes, twelve projects, six cheatsheet, 40 DSA, twelve packaging, 23 data analysis, 22 web and fifteen testing. The updated source archive contains 292 files: 280 programs, nine tests, README, manifest and requirements. Its byte size and SHA-256 are recorded in `NINTH-PASS-VALIDATION.json`.

The browser passed 315 desktop Python routes, 560 mobile article views at 320px and 390px, all 252 quiz answers, downloads and cross-subject navigation. A long lesson title initially overflowed at 320px; the title wrapping was fixed and the entire mobile sweep passed. One Contents-dialog timeout in the next full attempt did not recur in a route-diagnostic mobile rerun. The local production build passed 756 public response checks, 625 ready records, a 626-URL sitemap including home, nine noindex utility routes and four invalid/archived 404 checks without transport retries. TypeScript, the production build and whitespace checks passed. These tests do not establish live crawlability, indexation, traffic or ranking.

## Research and boundaries

The seven requested pages were checked in the supplied order for curriculum breadth. The PSF page describes the foundation rather than a language tutorial. The GeeksforGeeks page returned an access error in this pass, so earlier readable scope notes were used; its text or layout was not copied. W3Schools, Edube and Codecademy offered readable scope context. Codedex and Kaggle did not expose a readable lesson body in this research pass. Technical contracts were checked against primary Python, packaging, NumPy and pandas documentation and the executed programs. These URLs are retained for editorial traceability, not inserted into public tutorial bodies:

- https://www.python.org/psf-landing/
- https://www.geeksforgeeks.org/python/python-programming-language-tutorial/
- https://www.w3schools.com/python/
- https://www.codedex.io/python/01-setting-up
- https://edube.org/study/pe1
- https://www.codecademy.com/catalog/language/python
- https://www.kaggle.com/learn/python
- https://docs.python.org/3/library/unittest.html
- https://docs.python.org/3/library/asyncio-task.html
- https://docs.python.org/3/library/importlib.metadata.html
- https://docs.python.org/3/library/argparse.html
- https://docs.python.org/3/library/functools.html
- https://packaging.python.org/en/latest/specifications/version-specifiers/
- https://pandas.pydata.org/docs/reference/api/pandas.merge_asof.html
- https://numpy.org/doc/stable/reference/generated/numpy.isfinite.html

Python remains open-ended. Broader interviews and exercises need editorial review and a hosted judge. Web examples need real authentication, tenant boundaries, deployment concurrency and persistent application wiring. Data analysis needs measured larger datasets and domain-specific checks. Packaging needs authenticated release provenance, full archive verification and platform matrices. DSA needs sparse and large-input profiling. Testing needs whole-project mutation/typing and actual multi-version CI. Quizzes keep browser-local progress. The WordPress import, purchased domain, DNS, live deployment and live SEO verification remain separate launch work. The branch is a draft review branch; no main merge, CMS import or live deployment is included. Courses stay archived.
