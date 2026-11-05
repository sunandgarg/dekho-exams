# Python expansion, eleventh pass — 30 September 2026

This pass adds fourteen original lessons and one twelve-question quiz. Python now has 310 article pages, fourteen section hubs, 23 quiz banks and 276 questions across 347 canonical Python routes. The lessons cover ambiguous JSON and CSV keys, strict UTF-8, exact decimal input, shallow object ownership, SQLite uniqueness and replay updates, four bounded algorithms, and a staged JSONL-to-SQLite project. Prose and code are original teaching fixtures, not copied examples with changed values. Python semantics, public API behavior and algorithmic ideas are not exclusive AI Trove property.

The generator adds related links and reciprocal links from twelve existing pages. Python bodies contain 2,607 internal links to 382 distinct targets. The Java, Spring and Python learning set has 655 routes and 3,838 body links with zero broken or unpublished destinations. All Python articles and quizzes appear in their section modules; no Python page is orphaned.

## New pages

- Data intake: duplicate JSON names; duplicate CSV headers; malformed UTF-8 and an unexpected BOM; an Inexact decimal trap.
- Object state: dataclasses.replace sharing a list; dictionary union sharing nested values; an unhashable-list-in-a-tuple interview trace.
- SQLite: nullable UNIQUE fields; an explicit ON CONFLICT update showing why an upsert alone is not idempotency.
- Algorithms: sliding-window maxima with a monotonic deque; 0-1 BFS; exact running medians; binary search over a monotone capacity predicate.
- Project: validate and stage a bounded JSONL batch before one SQLite transaction.
- Quiz: twelve explained questions on these boundaries.

The local route map is /learning-coverage.html?subject=Python. The first new lesson is /python/json-duplicate-keys; the project is /python/validated-jsonl-ledger-project.

## Verification

All 310 article programs ran in isolated temporary directories on CPython 3.14.6 and exactly matched displayed output. Their syntax parses under the 3.11 grammar; this does not prove execution on 3.11. Eleven Python source-kit test files pass 120 suites and 151,004 bounded oracle comparisons. The seven new suites add 2,600 comparisons, including independent references for sliding maxima, binary-weight graph paths, prefix medians and ordered shipment capacity. They also test duplicate fields, malformed bytes, amount exactness, aliases and a rolled-back batch.

The 324-file source ZIP is 210,706 bytes, with SHA-256 d0f6916d633dd48f8eefdc878a83f724d7d8a1160c106524f3f76b26da9ccd81. TypeScript, production build and whitespace checks pass. A local browser check opened every new article and quiz route: all displayed their heading, articles showed one Python code block and Common Mistakes, no checked desktop route overflowed, and the quiz opened its attempt screen. Four representative routes also showed no overflow at a 390-pixel mobile viewport, with the article contents control visible. The local review URL returns 200 and X-Robots-Tag: noindex, follow. The full older cross-device browser sweep and launch-mode SEO sweep were not repeated in this pass; this browser comparison covers the fifteen added routes. The production build still warns that some generated chunks exceed 500 kB.

## Research and limits

The seven supplied URLs were revisited in order. The PSF landing page is about the foundation and infrastructure, not a language tutorial. GeeksforGeeks was readable for its topic map and page pattern on this pass; no prose, examples, images or visual identity were copied. W3Schools, Edube and Codecademy were scope checks. Codédex exposed no readable lesson body and Kaggle returned no page text through the research tool, so neither was used for technical claims. New lesson behavior was checked against official Python documentation for json, csv, codecs, decimal, dataclasses, sqlite3 and collections, then tested in runnable fixtures. Source URLs are editorial research records, not links inside public tutorial bodies:

- https://www.python.org/psf-landing/
- https://www.geeksforgeeks.org/python/python-programming-language-tutorial/
- https://www.w3schools.com/python/
- https://www.codedex.io/python/01-setting-up
- https://edube.org/study/pe1
- https://www.codecademy.com/catalog/language/python
- https://www.kaggle.com/learn/python
- https://docs.python.org/3/library/json.html
- https://docs.python.org/3/library/csv.html
- https://docs.python.org/3/library/codecs.html
- https://docs.python.org/3/library/decimal.html
- https://docs.python.org/3/library/dataclasses.html
- https://docs.python.org/3/library/sqlite3.html
- https://docs.python.org/3/library/collections.html

Python and its ecosystem are not exhaustive. The importer uses an already received bounded string and in-memory SQLite; it does not enforce an HTTP reception cap or prove crash durability. The 0-1 BFS and median fixtures are small and unprofiled. Larger data workloads, advanced async scheduling, packaging provenance, multi-version CI, more exercises/interviews and a hosted code judge still need work. Quiz progress remains browser-local. WordPress import, a purchased domain, DNS, live deployment and search-index/ranking verification remain separate launch tasks. This branch remains a draft PR and has not been merged or deployed.
