# Python expansion, second pass — 29 September 2026

The review branch adds 40 original lessons, three explained quiz banks and Packaging & Tools, Data Analysis and Web Applications section tabs. Python now contains 89 tutorial articles, 13 section hubs and seven twelve-question banks: 109 canonical Python routes and 84 questions. The tutorial bodies use semantic HTML, a technical definition first, one runnable program, displayed output, explicit contracts/costs, Common Mistakes and deliberate internal links. No tutorial was produced by replacing identifiers in a reference example. Research checks facts and scope; explanations, datasets and programs are authored for AI Trove. Neither exclusive rights in language facts/API syntax nor human authorship/detector invisibility is claimed.

## Coverage added

- Foundations: enclosing names and late binding; keyword unpacking/collisions and strict record pairing.
- Collections: deep-copy alias relationships, NFC equivalence, Counter/deque ownership and repeated timezone clocks.
- Advanced: iterator protocol, descriptor precedence, cooperative MRO, Protocol annotations, spawned process workers, subprocess arguments/exit codes, lock-protected transitions, queue completion accounting and asynchronous deadline cleanup.
- Algorithms: stable merge sort, topological dependency order, bounded nonnegative Dijkstra, union-find, a bounded trie, prefix-function overlapping search, rolling-row LCS, 0/1 knapsack value, prevalidated linked-list reversal and iterative tree traversal with repeat rejection.
- Practice/projects: iterator execution traces, staged rollback exercise, byte/row/field-bounded CSV, transactional SQLite batches with clean file reopen, and staged file replacement with failure cleanup.
- Packaging: src-layout package entrypoint and an offline wheel build with metadata inspection.
- Data analysis: NumPy view/copy ownership and shape broadcasting; Pandas nullable integer/missing amounts and join cardinality.
- Web: introductory Flask routing/request validation and Django routing/form cleaning using local test clients/forms. These examples do not start a network server.

## Verification and interpretation

All 89 public programs executed with their exact displayed output on CPython 3.14.6. Their source syntax also parsed with the 3.11 grammar; that is not execution on Python 3.11. Third-party examples were executed in an ignored project-only virtual environment, with their direct versions on the lesson and the full tested package snapshot in requirements.txt. Dependency-bearing examples claim the tested Python 3.14.6 environment, not older-runtime compatibility. The environment includes NumPy 2.5.3, Pandas 3.0.6, Flask 3.1.3, Django 5.2.17, build 1.6.1 and setuptools 84.0.0. These versions document the test, not a recommendation to pin them forever. No dependency was installed into the website runtime or system Python.

The original ten suites passed again (2,250 independent oracle comparisons). Fifteen new suites passed with 3,715 independent comparisons: stable builtin sorting, all-pairs shortest paths, enumeration of legal dependency orders, graph reachability versus union operations, repeated builtin overlapping string search, enumerated subsequences, enumerated cargo subsets, set-based trie answers and node identity after reversal. Other checks cover rejection before mutation, descriptor state preservation, invalid CSV fields/budgets, SQL rollback/clean reopen, injected file replacement failure/cleanup and Flask body/schema/media-type boundaries. The scope and counts are recorded in SECOND-PASS-VALIDATION.json. Browser/build/sitemap evidence is appended after those checks finish.

There are 745 Python tutorial/hub/quiz body links: 704 to Python entries, 38 to Java and three to Spring. Forty-nine specific links from 28 existing Python lessons connect their operation boundaries to the new material. All body targets exist and are published; link density is not a search-ranking promise. Every lesson and quiz belongs to its section modules. Tutorial links stay outside runnable source.

The source archive contains 89 page programs, two test files, manifest.json, README.md and requirements.txt: 94 files. No interpreter, dependency binaries, cached bytecode, real credential or private configuration is included. Third-party projects retain their licences. The pinned requirements snapshot is not a cross-platform wheel lock or hash-verified supply-chain guarantee.

## Reference handling

The seven requested pages were reviewed in the user's stated order. The PSF landing page concerns the foundation/community, so technical verification uses Python documentation. GeeksforGeeks supplied broad section-scope ideas rather than prose, code, graphics or an exact reproduction of its curriculum. W3Schools, Edube and Codecademy provided only scope comparisons. Codedex and Kaggle returned no useful readable lesson body in this fetch and were skipped without repeated attempts. Reference prose/code was not inserted into public lessons; changing sample values is not an originality method.

Requested scope references:

- https://www.python.org/psf-landing/
- https://www.geeksforgeeks.org/python/python-programming-language-tutorial/
- https://www.w3schools.com/python/
- https://www.codedex.io/python/01-setting-up
- https://edube.org/study/pe1
- https://www.codecademy.com/catalog/language/python
- https://www.kaggle.com/learn/python

Technical references, kept in this editorial handoff:

- https://docs.python.org/3/reference/datamodel.html
- https://docs.python.org/3/library/copy.html
- https://docs.python.org/3/howto/descriptor.html
- https://docs.python.org/3/library/typing.html
- https://docs.python.org/3/library/unicodedata.html
- https://docs.python.org/3/library/zoneinfo.html
- https://docs.python.org/3/library/itertools.html
- https://docs.python.org/3/library/concurrent.futures.html
- https://docs.python.org/3/library/subprocess.html
- https://docs.python.org/3/library/threading.html
- https://docs.python.org/3/library/asyncio-queue.html
- https://docs.python.org/3/library/sqlite3.html
- https://docs.python.org/3/library/tempfile.html
- https://docs.python.org/3/library/os.html
- https://packaging.python.org/en/latest/tutorials/packaging-projects/
- https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
- https://numpy.org/doc/stable/user/basics.indexing.html
- https://numpy.org/doc/stable/user/basics.broadcasting.html
- https://numpy.org/doc/stable/reference/generated/numpy.shares_memory.html
- https://pandas.pydata.org/docs/user_guide/missing_data.html
- https://pandas.pydata.org/docs/user_guide/merging.html
- https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.merge.html
- https://flask.palletsprojects.com/en/stable/testing/
- https://flask.palletsprojects.com/en/stable/quickstart/
- https://flask.palletsprojects.com/en/stable/web-security/
- https://docs.djangoproject.com/en/5.2/topics/testing/tools/
- https://docs.djangoproject.com/en/5.2/topics/http/urls/
- https://docs.djangoproject.com/en/5.2/ref/forms/validation/
- https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/pages/lecture-notes/
- https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/6277a1f06100c26a7ff21031af6757b5_MIT6_006F11_lec16.pdf
- https://cp-algorithms.com/data_structures/disjoint_set_union.html
- https://cp-algorithms.com/string/prefix-function.html
- https://cp-algorithms.com/dynamic_programming/knapsack.html

API facts were verified against official project documentation. Algorithm invariants and the specific implementation costs are also checked through independent small-input oracles; no reference program or illustration is copied. Current stable documentation may describe patches newer than the actual tested environment, so exact behavior claims are tied to the recorded installed versions/output tests.

## Remaining work

This pass does not exhaust Python or its ecosystem. The detailed per-section map is /learning-coverage.html?subject=Python and docs/learning-coverage/COVERAGE-AND-REMAINING.md. Remaining curriculum includes metaclasses/slots/buffer protocols, static checker runs, free-threaded and cross-platform testing, advanced numerical/ML/scientific material, larger data/aggregation/windowing/plotting workflows, Django ORM/models/migrations/templates, web identity/CSRF/tenant rules, async web stacks, packaging/release automation, and more interview/exercise/algorithm material.

The new SQLite project checks local disk persistence after clean close and transaction rollback, not power-loss recovery. Staged file publication checks old-state preservation and candidate cleanup, not crash durability or hostile-directory safety. Subprocess fixtures have fixed tiny output; they do not enforce arbitrary child-output/process-tree budgets. The data lessons have declared small shapes and values, not a production import pipeline. Local test clients/forms establish application behavior, not a deployed Python service.

WordPress import/verified CMS origin, purchased-domain canonical configuration, editorial launch review, production indexability switch and deployed checks remain launch work. Authenticated progress and hosted code judging need backend services. Preview remains noindex. Main and the live Cloudflare site are unchanged; content is prepared on the existing review branch.

## Reproduce

Run python3 work/python-content.py, then python3 scripts/check-python-content.py with work/python-env/bin/python containing requirements.txt. Run both test files (the expansion suite uses that environment), then scripts/write-python-kit.py and scripts/write-learning-coverage.py. The generator owns the Python section, its foundation path and specific reciprocal link sections. Course fixtures remain hidden behind their existing flag. Public content is still provided through existing CMS page templates and canonical catch-all routing; no separate page component is required for every topic.

## Browser and build checks

The browser sweep passed all 109 Python canonical routes on desktop and all 89 articles at both 320 and 390 pixels (178 mobile article views). All 84 quiz answers/results were exercised. Mobile lesson and heading jumps, resource-tab selection, syntax highlighting, source download, search, the 16-card homepage and sample Java/Spring pages passed with no browser page errors. NumPy desktop and Flask mobile screenshots were visually inspected. TypeScript, production compilation, targeted lint (zero errors/warnings) and whitespace checks passed. These are local checks; no field performance or search-ranking result is claimed.

Locally served launch-mode HTML passed checks for all 550 public non-course fixture entries: one H1/title, canonical origin, indexing eligibility and structured data. All 419 ready records plus home appear exactly once in the 420-URL sitemap. Nine utility/attempt/result routes, source downloads and coverage maps remain noindex; four invalid/course routes are 404 and the canonical alias redirects with 308. This is a local launch simulation, not a deployed SEO check or a guarantee of ranking. The reviewer preview is restored to noindex with an empty sitemap.
