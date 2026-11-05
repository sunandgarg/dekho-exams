# Python expansion, third pass — 29 September 2026

This pass adds 34 original articles, three twelve-question quiz banks and a Testing & Quality section. Python now has 123 articles, 14 hubs and ten quiz banks: 147 canonical routes and 120 explained questions. The new bodies begin with a definition and contain an operation contract, ownership/failure boundaries, a standalone program, displayed output, costs, Common Mistakes and internal links. They use semantic HTML. Links stay outside executable code. Reference examples were not copied and renamed; explanations, datasets and programs were written for AI Trove. Language facts, API syntax and dependencies are not exclusive AI Trove property, and no human-authorship or detector-invisibility claim is made.

## Material added

- Values and types: shared memoryview buffers/release, hash/equality contracts and wire-value enums.
- Object lifetime: slots, weak-value caches and partially acquired resource cleanup through ExitStack.
- Core/application boundaries: bounded recursion, TOML schema checks, source precedence before publication and allowlisted audit fields.
- Algorithms: rolling-row edit distance, distinct-symbol windows, signed shortest paths with reachable negative-cycle rejection, minimum spanning forests, point-replacement range sums and unbalanced BST deletion.
- Data: missing-key/all-null group totals, row-count rolling windows, chunked CSV accumulation with later-batch rejection, finite-value/tolerance checks and headless labeled PNG rendering.
- Model evaluation: training-only preprocessing in a pipeline and explicitly ordered classification error counts. Fixture predictions are not a business-quality claim.
- Testing: owned Pytest files/parameterized failures, expected Mypy diagnostics and an injected synchronous writer failure before local publication.
- Django: database constraints, measured foreign-key query counts, batch rollback/on_commit timing, an actual generated/applied initial migration for an owned installed app, HTML text autoescaping, enforced local CSRF and bounded ID-cursor pages.
- Project: sequential SQLite request identity with matching replay reuse and conflicting replay rejection. No exactly-once external effect is claimed.

## Checked scope

All 123 public programs execute with their exact displayed output on CPython 3.14.6. Syntax also parses under the 3.11 grammar; that is not execution on 3.11. Dependency-bearing lessons state their tested package versions and claim the tested 3.14.6 environment. The ignored project-only environment adds Matplotlib 3.11.2, scikit-learn 1.9.1, Pytest 9.1.1 and Mypy 2.3.1 to the earlier recorded dependencies. The full environment snapshot is in the source kit's requirements.txt. Nothing was installed into system Python or the website's runtime. The checker allows 45 seconds per isolated program to accommodate cold imports/font discovery; it does not weaken exact-output assertions.

All previous 25 suites passed again, with 5,965 independent comparisons. Nine new suites passed with 10,388 comparisons: recursive edit search, all-substring window enumeration, all-pairs signed graph paths/cycle checks, enumerated forest subsets, direct range sums, sorted key sets after tree deletion and standard-library group accumulation. Rejection checks cover malformed/bounded inputs, booleans, an unreachable negative cycle, loops/parallel edges, invalid replacement without mutation, late CSV rejection, unchanged configuration sources and conflicting job replays. Combined: 34 suites and 16,353 oracle comparisons. Pytest's four example cases and the tool/database/request checks inside the public programs are separate from that oracle count.

There are 1,036 Python body links, including 995 to Python lessons/hubs/quizzes, 38 to Java and three to Spring. Twenty-four existing Python lessons gain specific reciprocal pointers to these new boundaries. All 2,267 learning-body link targets across Java, Spring and Python exist and are published. Links are contextual connections, not a ranking guarantee. Every Python article/quiz belongs to a section module, and the hub/sidebar query caps remain respected.

The source ZIP has 129 files: 123 page programs, three test files, manifest.json, README.md and requirements.txt. Source bytes match the checked kit files. No interpreter, dependency binary, cached bytecode or private configuration is included. Dependencies retain their licences; this snapshot is not a cross-platform or hash-verified wheel lock.

## Research handling

The seven requested pages were revisited in the stated order. The PSF landing page supplies foundation/community context. GeeksforGeeks, W3Schools, Edube and Codecademy informed broad scope comparisons, not copied prose, programs, graphics or exact curriculum reproduction. Codedex and Kaggle supplied no useful readable lesson body in these fetches and were skipped without retries. Technical behavior was checked against primary project documentation. Current documentation patches can differ from the recorded installed test versions.

Requested scope references:

- https://www.python.org/psf-landing/
- https://www.geeksforgeeks.org/python/python-programming-language-tutorial/
- https://www.w3schools.com/python/
- https://www.codedex.io/python/01-setting-up
- https://edube.org/study/pe1
- https://www.codecademy.com/catalog/language/python
- https://www.kaggle.com/learn/python

Technical references retained here for editors rather than in public tutorial bodies:

- https://docs.python.org/3/reference/datamodel.html
- https://docs.python.org/3/library/contextlib.html
- https://docs.python.org/3/library/weakref.html
- https://docs.python.org/3/library/tomllib.html
- https://docs.python.org/3/library/unittest.mock.html
- https://docs.djangoproject.com/en/5.2/topics/db/models/
- https://docs.djangoproject.com/en/5.2/topics/db/transactions/
- https://docs.djangoproject.com/en/5.2/topics/migrations/
- https://docs.djangoproject.com/en/5.2/topics/db/optimization/
- https://docs.djangoproject.com/en/5.2/topics/templates/
- https://docs.djangoproject.com/en/5.2/ref/csrf/
- https://pandas.pydata.org/docs/user_guide/groupby.html
- https://pandas.pydata.org/docs/user_guide/window.html
- https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
- https://numpy.org/doc/stable/reference/generated/numpy.isclose.html
- https://matplotlib.org/stable/users/explain/figure/backends.html
- https://scikit-learn.org/stable/common_pitfalls.html
- https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html
- https://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html
- https://docs.pytest.org/en/stable/how-to/tmp_path.html
- https://docs.pytest.org/en/stable/how-to/assert.html
- https://mypy.readthedocs.io/en/stable/getting_started.html
- https://mypy.readthedocs.io/en/stable/command_line.html
- https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.csgraph.bellman_ford.html
- https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.csgraph.minimum_spanning_tree.html

## Remaining work and publishing boundaries

Python is not exhausted by this pass. The section map at /learning-coverage.html?subject=Python and docs/learning-coverage/COVERAGE-AND-REMAINING.md lists current pages and remaining material for every section. Gaps include metaclasses, further descriptors/typing, balanced trees/trie deletion, wider DP reconstruction, time-based data windows, larger scientific/ML workflows, further interview/exercise/reference material, property-based/mutation testing, cross-platform/free-threaded runs and release automation.

Web gaps include real identity and tenant authorization, production database concurrency and backfills, Flask persistence, deployment/proxy behavior and async web stacks. The ORM fixture uses owned SQLite state; the migration is a tiny initial app schema, not proof of a safe large-table alteration. HTML text escaping is not URL/JavaScript encoding. A valid CSRF token is not authorization. Cursor pages are not snapshots across requests. Commit callbacks are not durable delivery. The job ledger is sequential and local, not a competing-writer or remote-payment system.

WordPress import and a verified CMS origin, purchased-domain canonical configuration, editorial launch review, production indexing switch and deployed checks remain launch work. Authenticated progress and hosted code judging need backend services. Courses remain archived. Main and the live Cloudflare site remain unchanged; this pass stays on the review branch with a local noindex preview.

## Reproduce

Run python3 work/python-content.py, then python3 scripts/check-python-content.py with work/python-env/bin/python containing the pinned requirements. Run test_contracts.py, test_expansion.py and test_depth.py with the recorded interpreter/environment. Then generate the source ZIP and coverage/export files with scripts/write-python-kit.py and scripts/write-learning-coverage.py. The third-pass helper executes before hub/module assembly, so regeneration preserves the added pages, banks and reciprocal pointers. Existing canonical page templates and catch-all routing serve all topics; no per-article route component is required.

Browser/build/launch-mode checks and final source fingerprints are recorded in THIRD-PASS-VALIDATION.json after verification.

## Browser and build verification

The browser sweep passed all 147 Python routes on desktop and all 123 articles at both 320 and 390 pixels (246 mobile views). It exercised all 120 quiz answers/results, the mobile lesson and heading jumps, selected resource tabs, code highlighting, source/map download headers, search, the 16-card homepage and representative Java/Spring pages. No browser page errors occurred. Django query-count desktop and model-pipeline mobile screenshots were visually inspected. TypeScript, production compilation and whitespace checks pass. Lint of the changed browser checker has no findings; a wider template check has zero errors and one existing react-refresh export warning in templates.tsx, which this pass does not alter.

Locally served launch-mode HTML passed metadata/indexability checks for all 588 public non-course entries. The sitemap contains exactly 458 eligible URLs: 457 ready records plus home. Nine utility/attempt/result checks and download/map headers remain noindex, four invalid/course routes return 404 and the canonical alias redirects with 308. This is a local launch simulation, not a deployed SEO check, field performance result or ranking guarantee. Port 3001 is restored to the noindex reviewer preview with an empty sitemap.
