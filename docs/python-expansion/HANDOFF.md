Latest Python expansion: [eleventh-pass scope and verification](ELEVENTH-PASS.md). Earlier passes remain historical snapshots.

# Python content pass

This document records the first-pass baseline. See [SECOND-PASS.md](SECOND-PASS.md) and the current learning coverage map for the expanded 89-article, 13-hub, seven-quiz curriculum.

This pass replaces four short starter articles and one three-question quiz with 49 original tutorials, ten section hubs and four twelve-question banks. Python remains a separate subject alongside Java and Spring & Spring Boot. There are 63 Python canonical routes, plus the revised ten-step Python foundations learning path.

## Learning skeleton

- Python Tutorial: 16 lessons on interpreter setup, name/object ownership, numeric operations, conditions, pattern matching, functions/arguments, exceptions, modules, formatting, annotations, comprehensions, slices and object state.
- Data Types & Collections: seven lessons on lists, tuples, dictionaries, sets, sorting, bytes/text and decimal money.
- Advanced Python: seven lessons on generators, decorators, closures, cleanup, dataclasses, structured asynchronous work and threads.
- Interview Questions: one original identity/default-argument tracing review.
- Exercises: two input and collection validation tasks.
- Examples: eight programs on JSON, CSV, paths/files, SQLite, logging, regex field contracts, timestamps and unittest.
- Quizzes: four explained banks covering foundations, collections, runtime boundaries and algorithm contracts; 48 questions total.
- Projects: a receipt CLI and staged in-memory inventory ledger.
- Cheatsheet: one selected-operation reference with strict sequence-length checks.
- DSA in Python: boundary search, BFS, heap selection, bracket nesting and cached minimum-package counts.

The generated `docs/learning-coverage/COVERAGE-AND-REMAINING.md` and local `/learning-coverage.html?subject=Python` are the current skeleton maps. They state unfinished work per section. Earlier Java/Spring reports remain release snapshots.

## Content and research

Tutorial bodies contain original semantic HTML, internal lesson links, one runnable program, stated output, operation/input/ownership limits, cost discussion and a Common Mistakes section. No external sources, tables or Markdown appear in these public bodies. Links remain outside executable code. The Python curriculum adds 391 HTML body links, including 37 links to Java contracts; fourteen Java pages and one Spring page link back. All targets are published eligible routes in the local fixture export.

The supplied priority sites were reviewed in order for relevance and curriculum scope. The PSF landing page concerns the foundation/community, so language and standard-library contracts were checked against official Python documentation. GeeksforGeeks informed the broad hub/section/lesson model; its prose, programs, images and exact curriculum were not copied. W3Schools, Edube and Codecademy were scope checks rather than technical authorities. Codedex and Kaggle provided insufficient readable page content through the research tool and were skipped without repeated attempts.

Official contracts were checked against the Python 3.13 documentation. The actual program execution baseline is CPython 3.14.6; this is not a claim to use the latest Python release. Programs parse with the 3.11 grammar, but were not runtime-tested on 3.11, PyPy, free-threaded builds or every platform.

Fresh prose and programs were written for AI Trove. Renaming values in a copied example is not the workflow used here. Python facts, API syntax, general algorithms, third-party brands and dependencies are not exclusive AI Trove property. This pass does not guarantee copyright exclusivity, human authorship or AI-detector outcomes.

Research URLs, kept out of public tutorial bodies:

- https://www.python.org/psf-landing/
- https://www.geeksforgeeks.org/python/python-programming-language-tutorial/
- https://www.w3schools.com/python/
- https://www.codedex.io/python/01-setting-up
- https://edube.org/study/pe1
- https://www.codecademy.com/catalog/language/python
- https://www.kaggle.com/learn/python
- https://docs.python.org/3.13/tutorial/
- https://docs.python.org/3.13/tutorial/controlflow.html
- https://docs.python.org/3.13/tutorial/datastructures.html
- https://docs.python.org/3.13/tutorial/classes.html
- https://docs.python.org/3.13/tutorial/errors.html
- https://docs.python.org/3.13/library/stdtypes.html
- https://docs.python.org/3.13/reference/compound_stmts.html
- https://docs.python.org/3.13/howto/sorting.html
- https://docs.python.org/3.13/library/collections.html
- https://docs.python.org/3.13/library/asyncio-task.html
- https://docs.python.org/3.13/library/concurrent.futures.html
- https://docs.python.org/3.13/library/dataclasses.html
- https://docs.python.org/3.13/library/contextlib.html
- https://docs.python.org/3.13/library/decimal.html
- https://docs.python.org/3.13/library/heapq.html
- https://docs.python.org/3.13/library/json.html
- https://docs.python.org/3.13/library/csv.html
- https://docs.python.org/3.13/library/pathlib.html
- https://docs.python.org/3.13/library/sqlite3.html
- https://docs.python.org/3.13/library/argparse.html
- https://docs.python.org/3.13/library/logging.html
- https://docs.python.org/3.13/library/typing.html
- https://docs.python.org/3.13/library/unittest.html
- https://docs.python.org/3.13/library/datetime.html
- https://docs.python.org/3.13/library/re.html

## Reproduction and source downloads

From the app root:

1. `python3 work/python-content.py` upserts this curriculum and the reciprocal links. It preserves other subjects, canonical starter URLs and archived courses.
2. `python3 scripts/check-python-content.py` validates semantic HTML, internal targets, module coverage and all 49 exact program outputs. It extracts the same sources into `work/python-kit`.
3. `python3 -I work/python-kit/test_contracts.py` runs ten boundary/oracle suites. There are 1,000 bisect comparisons, 1,000 forward-layer minimum-package comparisons and 250 all-pairs graph comparisons, plus rejected input and state-preservation cases.
4. `python3 scripts/write-python-kit.py` packages the 49 programs, tests, manifest and README. The source ZIP has 52 files and no interpreter, bytecode, private configuration or dependencies.
5. `python3 scripts/write-learning-coverage.py` regenerates the three-subject learning map and reviewed fixture exports. This writer no longer rebuilds the unrelated Spring source archive.
6. `node scripts/check-python-browser.mjs` uses the configured Playwright module for canonical page, mobile, highlighted code, download, navigation and quiz checks.

`outputs/aitrove-python-content.json` is the Python-only content export. `outputs/aitrove-reviewed-content.json` contains the current publish-eligible fixture set. WordPress remains the intended admin/publishing source; exporting fixtures does not import them into WordPress.

The local source kit is served at `/downloads/aitrove-python-source-kit.zip`. Utility downloads and coverage pages retain noindex headers. Lessons do not run Python in the browser; quiz state is local. SQLite, the inventory ledger, temporary-file examples and task fixtures do not claim a durable deployed service or real network load test.

## Still to do

This is a substantial first Python pass, not a complete language or ecosystem reference. Packaging/wheels, broader imports and static checking, descriptors/MRO, process pools/subprocess limits, real asynchronous network deadlines, broader algorithms, named-timezone ambiguity and crash-safe durable projects remain. NumPy, Pandas, data science, Django and Flask require their own authored tracks. Interviews and the cheatsheet have starter coverage rather than exhaustive banks.

CMS import/verified origin, domain/DNS, editorial review and live deployment remain separate launch work. This pass updates only the review branch and local preview; it does not merge main or change the hosted site.

## Final verification

49 displayed program outputs, ten boundary suites and 2,250 independent oracle comparisons pass. Browser checks cover 63 canonical desktop screens, 98 mobile lesson views at 320/390 pixels, all 48 quiz answers/results, mobile lesson and heading jumps, highlighted Python code, search, downloads and the 16-card homepage. The unchanged successful page sweeps are fingerprinted so flow-only retries cannot reuse results after page-source changes. Two test selectors were corrected for numbered heading links and optional downloads on older Java pages; no application changes were hidden by those retries.

TypeScript, production build and whitespace checks pass. Targeted lint has zero errors and one existing Fast Refresh warning. All 504 public fixture pages have checked status/title/canonical/robots/structured-data behavior. The built launch-mode sitemap contains 374 eligible URLs, with quiz attempts/results and utility pages excluded. These are local readiness checks, not proof of live indexation or ranking.

The local review site is restored on port 3001 with preview noindex enabled. Production deployment and CMS import were not performed.
