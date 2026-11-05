# Python expansion, fifth pass — 29 September 2026

This pass adds 34 original articles and three twelve-question quiz banks. Python now has 195 articles, 14 hubs and 16 quiz banks: 225 canonical routes and 192 explained questions. The tutorial bodies begin with a technical definition and include input/ownership/failure contracts, one standalone program and displayed output, costs, Common Mistakes and deliberate internal links. Bodies use semantic HTML; executable source contains no hyperlink markup. Explanations, fixtures and programs were written for AI Trove. General facts, API syntax, algorithms and third-party projects are not exclusive AI Trove property. No human-authorship, detector-invisibility or search-ranking guarantee is made.

## Material added

- Core: parser keywords versus wire identifiers, first-class callable dispatch, refactoring accepted/rejected contracts, and import failure side effects that survive module-cache removal.
- Collections: numeric byte arrays with exported-view resize limits, OrderedDict access order/equality, and adjacent groupby/strict zip/consumption contracts.
- Advanced: cooperative subclass hooks, deterministic closure of an async producer on early exit, and TypeGuard narrowing invalidated by a mutable alias.
- Algorithms: AVL deletion with ancestor repair, directed strongly connected components, edge-ID-aware bridges accepting parallel edges/self-loops, static compressed-trie exact membership, and odd/even-center palindrome substrings.
- Reception/storage: bounded binary JSON Lines with duplicate-key rejection and private result staging, two real SQLite connections contending for an immediate write transaction, and flat ZIP member/name/mode/actual decompressed-byte checks before owned writes.
- Projects: a transactional receipt/outbox pair with rollback and repeat-before-acknowledgement behavior; a bounded LRU with input validation before mutation; and a trusted owned-code plugin loader with interface checks before registry publication.
- Packaging: an owned offline wheel installed into a fresh temporary target and imported outside the source checkout; an actual temporary-target editable installation observed through fresh imports after a source edit. Nothing is installed into system or project site-packages.
- Data: duplicate-pair pivot policy, category validation before unknown labels become missing, and bounded seeded bootstrap means with explicit empirical-model limits.
- Testing: two selected wrong implementations detected by contract cases, and grammar parsing versus actual current-interpreter execution reported separately. These are not a whole-project mutation score or CI runtime matrix.
- APIs: visibility filtering before cursor paging; ownership assigned from the test principal during creation with received owner-field rejection; and fixed Flask error shapes preserving 404/405/413/500 without exposing internal exception text.
- Practice/reference: an actual SQLite WAL read-snapshot trace, duplicate-aware ledger reconciliation, and static annotation/TypedDict claims versus runtime validation.
- Three explained quiz banks: graph/index state changes, import/distribution contracts, and application publication boundaries.

The API rejection test exposed a serializer error-shape defect. Extra-field failures now use a dictionary-shaped non-field error so DRF can construct its declared 400 response. The earlier strict serializer lesson received the same correction, and a regression check reads its errors after rejection. Dependency setup prose now calls requirements.txt an environment snapshot rather than a complete lock.

## Checked program and contract scope

All 195 public programs execute in isolated temporary directories with exact displayed output on CPython 3.14.6. Syntax parses under the 3.11 grammar; this is not execution on 3.11. Dependency programs identify pinned packages. No new third-party package was needed. Packaging checks record pip 26.1.2, build 1.6.1 and setuptools 84.0.0. requirements.txt includes pip via freeze --all and records the complete tested environment; it is not a platform-independent or hash-verified wheel lock.

Eleven new suites pass with 53,000 independent comparisons: 18,000 mixed AVL insertion/removal states checked against sorted key sets plus structural ordering/height/balance assertions; 1,000 directed component partitions against mutual reachability; 1,000 bridge results against edge-removal connectivity; 10,000 compressed-trie lookups against word sets; 20,000 cache transitions against an independent access-order list; 2,000 palindrome results against all-substring enumeration; and 1,000 reconciliations against per-record searches. Failure checks cover Boolean/invalid graph endpoints, preserved rejected cache state, duplicate identities, exact stream byte/row budgets, malformed/duplicate JSON fields, caller stream ownership, ZIP names/modes/byte totals, outbox rollback, list bounds, anonymous creation, ownership spoofing, duplicate creation and readable serializer errors. Django/DRF cases run in separate interpreter processes because settings are process-wide.

All prior 45 suites pass again with 49,353 comparisons. Combined: 56 suites and 102,353 independent comparisons. Tool/API cases inside public examples and Hypothesis trials are separate from this oracle count.

Python bodies contain 1,623 internal links: 1,576 to Python lessons/hubs/quizzes, 38 to Java and nine to Spring. Thirty-five prior pages gain 48 reciprocal pointers. All 2,854 learning-body links across Java, Spring and Python resolve to published fixture entries; no broken or unpublished target was found. Every Python article/quiz belongs to a section module, with all section sizes below the query cap. These links represent related contracts, not a ranking promise.

The source ZIP contains 203 files: 195 programs, five contract-test files, manifest.json, README.md and requirements.txt. Archive bytes match the checked kit files. No interpreter, dependency binary, cached bytecode or private configuration is included. The full Java/Spring/Python learning export has 533 routes; 535 records in the full fixture set are marked ready for the local publish-mode checks.

All 225 Python routes pass desktop checks; all 195 articles pass at 320px and 390px. All 192 quiz answers pass through attempts/results, with no browser page errors observed. TypeScript, production build, browser-script lint and whitespace checks pass. Local publish-mode checks validate 666 public responses, 535 ready records and 536 sitemap URLs, along with nine noindex utilities, four invalid/archived 404s and the alias redirect. The restored local preview has all 14 Python tabs, remains noindex and has an empty sitemap. Evidence is recorded in FIFTH-PASS-VALIDATION.json. A local publish-mode build does not establish deployed behavior, search-engine submission or ranking.

## Current learning skeleton

- Tutorial: 31 articles.
- Data Types & Collections: 20 articles.
- Advanced Python: 27 articles.
- Interview Questions: six articles.
- Exercises: seven articles.
- Examples: 15 articles.
- Quizzes: 16 banks, 192 explained questions.
- Projects: eight articles.
- Cheatsheet: four articles.
- DSA in Python: 30 articles.
- Packaging & Tools: six articles.
- Data Analysis: 17 articles.
- Web Applications: 17 articles.
- Testing & Quality: seven articles.

Completed pages and unfinished work are generated in docs/learning-coverage/COVERAGE-AND-REMAINING.md and /learning-coverage.html?subject=Python. This is not an exhaustive Python ecosystem reference. Remaining curriculum work includes mutable compressed-edge updates, more algorithms and measured large inputs, larger application/interview tracks, real runtime/platform CI matrices, binary wheels and dependency resolution/security, full-project mutation tools, real identity/database-enforced tenant policies, async web deployment, scientific/ML specialization and dependence-aware uncertainty. Hosted execution and authenticated progress need backend services. CMS import, domain/DNS configuration, editorial launch review and production indexability remain launch work.

## Research handling

The seven requested pages were reopened in the stated order. PSF supplies foundation/community context. GeeksforGeeks, W3Schools, Edube and Codecademy informed scope comparison rather than copied prose, examples, graphics or exact page-tree reproduction. Codedex and Kaggle supplied no useful readable lesson body and were skipped without retries. Language and project behavior was checked against primary documentation and owned executable fixtures. Current Python documentation reports a newer patch than the tested runtime, so the lessons state the actual 3.14.6 execution environment.

Requested scope pages:

- https://www.python.org/psf-landing/
- https://www.geeksforgeeks.org/python/python-programming-language-tutorial/
- https://www.w3schools.com/python/
- https://www.codedex.io/python/01-setting-up
- https://edube.org/study/pe1
- https://www.codecademy.com/catalog/language/python
- https://www.kaggle.com/learn/python

Primary technical references retained here rather than in public tutorial bodies:

- https://docs.python.org/3/library/itertools.html
- https://docs.python.org/3/library/array.html
- https://docs.python.org/3/library/importlib.html
- https://docs.python.org/3/library/typing.html
- https://docs.python.org/3/reference/datamodel.html#object.__init_subclass__
- https://docs.python.org/3/library/asyncio-task.html
- https://docs.python.org/3/library/zipfile.html
- https://www.sqlite.org/isolation.html
- https://www.sqlite.org/lang_transaction.html
- https://packaging.python.org/en/latest/tutorials/packaging-projects/
- https://setuptools.pypa.io/en/latest/userguide/development_mode.html
- https://pip.pypa.io/en/stable/cli/pip_install/
- https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.pivot.html
- https://pandas.pydata.org/docs/user_guide/categorical.html
- https://numpy.org/doc/stable/reference/random/generator.html
- https://www.django-rest-framework.org/api-guide/generic-views/
- https://www.django-rest-framework.org/api-guide/serializers/#saving-instances
- https://docs.djangoproject.com/en/5.2/topics/testing/tools/
- https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/pages/lecture-notes/
- https://algs4.cs.princeton.edu/41graph/

The directed-graph and trie summary pages at Princeton returned a timeout/empty body in this fetch and were not used as factual evidence. The independently written graph/trie programs were checked against reachability/removal/set oracles. No reference implementation was copied or renamed.

## Publishing boundary

These are local review fixtures on the existing draft branch. WordPress remains the publishing authority; Cloudflare reads published CMS entries. The export and source kit are prepared for review/import. This pass does not merge main, deploy the live worker or import WordPress content. Courses remain archived behind the disabled feature flag. SQLite/Flask/DRF examples run locally, with test authentication explicitly identified; they do not create a hosted production Python backend.
