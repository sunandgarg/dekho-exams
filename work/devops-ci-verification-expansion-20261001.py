"""Add CI verification contracts to the local DevOps preview."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
course = "devops/devops-tutorial"
project_hub = course + "/project"
quiz_hub = "devops/quizzes"
specs = []


def lesson(slug, title, summary, definition, operation, language, sample, cost, mistakes, related):
    path = "devops/" + slug
    assert path not in by_path, path
    specs.append(dict(path=path, title=title, summary=summary, definition=definition,
                      operation=operation, language=language, sample=sample,
                      cost=cost, mistakes=mistakes, related=related))


lesson(
    "merge-queue-candidate-verification", "Merge queue checks: test the combined commit that will land",
    "Require a fresh result for the merge-group revision, not only pull-request heads.",
    "A merge queue constructs a candidate revision containing one or more accepted changes and the current base branch. Checks on each pull-request head do not prove that combined candidate works. A required workflow must run on the queue event and report against that candidate; otherwise the queue may wait for a result that never appears, or a team may weaken the gate to work around it.",
    "A receipt service and ledger library change pass separately, but their combined dependency graph breaks an integration test. Configure the required verification workflow to run for pull requests and merge groups. The fragment shows the event contract; the referenced script must build and test the checked-out revision, not fetch an earlier head. Log the revision, event type, dependency lock digest, and final artifact digest in the result. Submit two compatible-looking changes together and deliberately make their combination fail in a test repository; confirm the queue rejects the group while preserving each pull request for repair. Repeat after the base branch advances. If an external CI system reports the check, confirm it attaches the conclusion to the queue revision and has a stable check identity. Deploy only an artifact built from the accepted candidate or its resulting merge commit.",
    "yaml", "name: receipt-merge-verification\non:\n  pull_request:\n  merge_group:\n    types: [checks_requested]\njobs:\n  verify:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - run: ./ci/verify-receipt.sh",
    "A fresh combined build consumes CI capacity and adds queue latency, especially when several pull requests are grouped. That cost buys evidence about the revision that will actually enter the protected branch. Measure queue wait, group failure rate, reruns after base movement, and the gap between checked revision and released artifact. A green check with a mismatched revision is worse than a visible red check because it can authorize untested bytes.",
    ["Do not use only pull-request-head checks as proof that a merge group passes.", "Do not turn off a required check because its queue event is missing.", "Do not release an artifact from a different revision than the accepted candidate."],
    ["devops/git-change-control", "devops/continuous-integration", "devops/artifact-promotion", "devops/ci-deployment-concurrency"],
)

lesson(
    "selective-ci-test-fallback", "Selective CI: default to full verification when impact is uncertain",
    "Treat a changed-file map as an optimization with a failure-safe escape path.",
    "Selective CI runs a subset of checks based on the files or targets affected by a change. It reduces latency only if the impact map is accurate. Shared libraries, generated schemas, build scripts, lockfiles, and configuration can affect code outside their directory. A missing base revision or a rename can also make a diff incomplete. The safe contract is explicit: uncertainty triggers the complete suite before the change becomes releasable.",
    "A repository has receipt and payout services. A receipt-only edit can run a focused service suite, but changes to shared/, schemas/, ci/, or the dependency lock must run the complete suite. The Bash fragment checks that the base commit exists, then uses a conservative path rule. In a real pipeline, derive BASE_REVISION from the event's trusted base SHA and verify the checkout has enough history; do not let a pull-request script supply an arbitrary value that bypasses checks. Test the selector with a shared API rename, a deleted file, and a missing base commit. Compare focused and full results for a sampled set of changes over several weeks. Keep one required result whose completion means the selected checks actually ran; a skipped workflow can leave a required status pending, and an optional check that never starts is not evidence of success.",
    "bash", "set -euo pipefail\nbase_revision=${BASE_REVISION:?missing trusted base revision}\nif ! git cat-file -e \"${base_revision}^{commit}\" 2>/dev/null; then\n  ./ci/run-all-tests.sh\n  exit 0\nfi\nif ! changed_paths=$(git diff --no-renames --name-only \"$base_revision\" HEAD); then\n  ./ci/run-all-tests.sh\n  exit 0\nfi\nif [[ -n \"$changed_paths\" ]] && ! grep -Eqv '^receipt/' <<< \"$changed_paths\"; then\n  ./ci/run-receipt-tests.sh\nelse\n  ./ci/run-all-tests.sh\nfi",
    "Targeted checks save runner minutes but require continuous maintenance of the impact graph. A conservative rule spends more CPU on ambiguous changes; an aggressive rule saves minutes while letting faults cross service boundaries unseen. Measure full-suite sampling failures, selector fallback frequency, and false-negative incidents. Keep the full suite scheduled and available on demand. The fragment is a narrow illustration for a two-service repository; it must be expanded when new shared paths or generated outputs are introduced.",
    ["Do not treat a path filter as proof that unaffected code cannot break.", "Do not silently skip tests when the base revision is unavailable.", "Do not mark a required gate green when no test command ran."],
    ["devops/continuous-integration", "devops/git-change-control", "devops/ci-cache-boundaries", "devops/api-compatibility-window"],
)

lesson(
    "flaky-test-quarantine-contract", "Flaky tests: quarantine one failure mode with an owner and expiry",
    "Keep unreliable checks visible while preventing endless rerun approvals.",
    "A flaky test produces different results for the same relevant source and test environment. It may expose a real race, shared state, timing assumption, or dependency outage. A successful rerun does not prove the first failure was harmless. Quarantine can protect delivery while the cause is fixed, but an unbounded exclusion quietly removes coverage from the release gate.",
    "A payout settlement test fails one run in twenty after parallel workers are added. Preserve the first failure's logs, seed, worker order, dependency versions, and revision. Reproduce with fixed code and varied order and concurrency, then classify whether the cause is application behavior, test isolation, or infrastructure. If the release gate must proceed, move only this test to a nonblocking quarantine lane with a named owner, issue, expiry date, and user risk statement. Keep it running on every relevant revision and alert when its failure rate rises; do not delete it or blanket-retry the entire suite until green. The contract below makes the exception reviewable. Fix the cause, require consecutive clean runs on the original gate configuration, and restore the test to blocking status. A new failure signature should reopen triage rather than inherit the old exception.",
    "text", "Settlement test quarantine record\nTest: payout_does_not_commit_twice\nOwner: ledger reliability team\nFailure signature: parallel-run state collision\nRelease coverage: settlement smoke remains blocking\nQuarantine: nonblocking run on every candidate\nExpiry: next planned release window\nExit: isolate data; restore blocking gate after clean repetitions",
    "Quarantine lowers immediate queue delay but carries a measurable coverage debt. Blind reruns increase runner cost and can mask an intermittent production defect. Track first-run failure rate, pass-on-rerun rate, age of each exception, and incidents linked to quarantined behavior. A short expiry forces review; a permanent exception merely renames a missing test. Keep evidence retention long enough to compare failure signatures without storing customer data.",
    ["Do not treat a passing rerun as proof the original failure was noise.", "Do not quarantine an entire suite because one test is unstable.", "Do not leave a nonblocking test without owner, expiry, and replacement coverage."],
    ["devops/continuous-integration", "devops/incident-review-actions", "devops/policy-exception-expiry", "devops/trace-context-propagation"],
)

lesson(
    "ci-test-data-isolation", "CI test data: give each run an isolated ownership scope",
    "Prevent parallel workers and retries from sharing mutable records.",
    "An integration test that writes to a shared database, queue, object store, or account can affect another test run. The resulting failure depends on timing and execution order rather than the candidate code. Isolation requires a scope that follows the test through every external system and is removed after use. A unique name in one database table is insufficient if the same test also publishes to a common queue or reads a global cache.",
    "Two receipt branches test settlement against one staging database and intermittently see each other's rows. Give each run a validated identifier and a dedicated schema or disposable database, plus queue topic, object prefix, and idempotency-key namespace derived from that same identifier. The policy fragment lists the boundary. Run the same suite twice in parallel with overlapping customer IDs and verify that neither run can observe or consume the other's records. Force one run to crash before cleanup, then have a janitor remove only expired scopes after checking ownership and retention; never let a broad delete pattern reach another run or production. Where a third-party sandbox cannot create per-run accounts, serialize the dependent tests or replace that integration with a deterministic local substitute and retain a separate contract check. Capture the scope ID in failure reports, but keep secrets and customer payloads out of artifacts.",
    "text", "Receipt CI run scope\nIdentity: trusted run ID plus attempt number\nDatabase: isolated schema or disposable instance\nQueue: per-run topic or consumer group\nObjects: per-run prefix with owner tag\nCache and idempotency: same run namespace\nCleanup: exact scope only, after retention window\nFailure report: scope ID and revision, no customer data",
    "Disposable databases and queues cost time, storage, and service quota; shared resources are cheaper until they create false failures or data leakage. Scope cleanup also needs a failure path for canceled jobs. Measure cross-run collisions, orphaned scopes, cleanup latency, and the time needed to provision isolation. If tests must share one external sandbox, limit concurrency explicitly and document that bottleneck rather than pretending the test suite is parallel-safe.",
    ["Do not use a fixed customer ID across simultaneous runs.", "Do not clean up with a broad prefix that may match another run.", "Do not isolate only the database while sharing queues, caches, or external accounts."],
    ["devops/ephemeral-environment-controls", "devops/queue-consumer-reliability", "devops/http-idempotency-replay", "devops/flaky-test-quarantine-contract"],
)

lesson(
    "hermetic-ci-dependency-boundary", "Hermetic CI tests: declare every service and input the check consumes",
    "Replace hidden host and network dependencies with controlled fixtures.",
    "A test is hermetic when its result depends on declared source, build outputs, and controlled test resources rather than whatever happens to be on the runner or public network. An undeclared package, host timezone, mutable image tag, shared service, or external API can turn a stable code change into a different result tomorrow. Isolation is about knowing the inputs, not merely running in a container.",
    "A receipt integration suite passes on one runner because an old PostgreSQL daemon and an inherited configuration file happen to exist. Start from a clean runner image, provision an explicitly versioned disposable database, apply migrations, seed synthetic fixtures, and fail if an unexpected outbound connection occurs. The policy fragment records the expected inputs. Run the check twice with a cleared workspace and cache, then change runner host and timezone to see whether output remains valid. Pin the database image by immutable digest after it is reviewed; a mutable tag alone cannot prove the same server bytes were used. Give every test a writable temporary directory and never write into the source checkout. Keep one small, separately controlled external contract test if a real payment provider interaction is essential, and label failures of that path as dependency failures rather than silently blaming code.",
    "text", "Receipt integration input contract\nSource: checked revision and lockfile digest\nRuntime: declared toolchain image digest\nDatabase: disposable instance at approved image digest\nSchema: migrations from checked revision\nFixtures: synthetic and versioned\nNetwork: deny unexpected external endpoints\nWorkspace: clean checkout and unique temporary directory",
    "Provisioning fresh services and downloading pinned images can slow a cold run, while caches can recover much of that cost if they remain untrusted inputs. The larger payoff is fewer environment-only failures and stronger culprit identification. Measure cold and warm duration, unexpected network attempts, cache-hit dependence, and failures that reproduce on a clean runner. A hermetic integration check does not replace a separate production-path smoke test; each answers a different question.",
    ["Do not assume a container automatically makes a test hermetic.", "Do not let a mutable service image tag define the test database.", "Do not use a hidden runner daemon as an undeclared dependency."],
    ["devops/ci-cache-boundaries", "devops/self-hosted-runner-isolation", "devops/ci-test-data-isolation", "devops/container-image-builds"],
)

lesson(
    "ci-matrix-required-gate", "CI matrix gates: distinguish skipped, canceled, experimental, and passed",
    "Require every supported platform result before approving a release.",
    "A matrix expands one CI job into several platform or runtime variants. A green result for one variant does not establish that all supported variants passed. Cancellation from fail-fast, conditional skips, and nonblocking experimental rows can change what a summary check means. A release gate must state which matrix entries are required, how missing entries are detected, and when an experiment may fail without blocking.",
    "A receipt API ships on two operating-system architectures. Run the same contract suite on both supported runners and record each result by architecture. The fragment disables fail-fast so one failure does not erase evidence from the other row; it does not itself implement the final gate. Build a stable required summary job that waits for every supported row, rejects failure, cancellation, and absence, and publishes the revision and image digest it checked. Keep experimental rows separate from that summary rather than marking all failures nonblocking. Deliberately break one architecture, cancel another, and skip a row with a condition in a test repository; confirm the protected branch cannot accept any of those as a complete supported-platform pass. Compare matrix rows with the architectures actually present in the promoted image index. A green CI matrix on an architecture that is never deployed is less useful than a runtime test on every production target.",
    "yaml", "name: receipt-platform-check\non:\n  pull_request:\n  merge_group:\n    types: [checks_requested]\njobs:\n  platform-test:\n    strategy:\n      fail-fast: false\n      matrix:\n        runner: [ubuntu-24.04, ubuntu-24.04-arm]\n    runs-on: ${{ matrix.runner }}\n    steps:\n      - uses: actions/checkout@v4\n      - run: ./ci/test-receipt-contract.sh",
    "A full matrix multiplies runner minutes and can lengthen queue time; disabling fail-fast spends more after the first failure but preserves diagnostic evidence. The summary job adds a small amount of orchestration and needs careful handling of missing checks. Measure per-row duration, cancellation rate, supported architecture coverage, and differences between tested and shipped images. Runner labels and availability are environment-specific, so validate them against the repository's actual hosted or self-hosted runner pool before adopting the fragment.",
    ["Do not count a skipped or canceled supported row as passed.", "Do not mark a required architecture experimental to keep releases moving.", "Do not claim runtime coverage from a build-only matrix."],
    ["devops/multiarch-image-promotion", "devops/continuous-integration", "devops/merge-queue-candidate-verification", "devops/release-evidence-record"],
)

lesson(
    "tested-artifact-digest-binding", "Tested artifact identity: deploy the bytes that passed",
    "Carry one immutable digest from the verification job to promotion.",
    "A pipeline can test source code and then rebuild an image for production, producing different bytes after dependency resolution, timestamps, or base-image changes. The source revision alone does not prove which binary reached users. A release record needs the tested artifact digest, the verification result bound to that digest, and the exact digest selected for deployment. A mutable tag is only a pointer.",
    "A receipt image passes integration tests in CI. Push that image once to the registry, record its immutable digest, run the final tests against the pulled image by digest, and promote that same digest to staging and production. The policy fragment lists the acceptance record. Before a deployment, compare the requested digest with the tested subject and reject mismatches even when the tag or source revision matches. Simulate a tag update after testing and confirm the deployment still uses the original digest. If an image index serves multiple architectures, verify each referenced platform image and record the index digest as the release unit. Keep the old digest accessible through the rollback window. The attestation or evidence document must be produced by the trusted build path; an untrusted pull-request job should not be allowed to assert its own production approval.",
    "text", "Receipt promotion evidence\nChecked revision: immutable commit identifier\nTest subject: registry image digest\nSupported platforms: each child image checked\nPromotion target: same image or index digest\nAdmission result: digest and trusted builder match\nRollback: prior digest still pullable",
    "Digest-based promotion reduces surprise but requires registry retention and careful garbage collection. Pulling the image again for final tests adds network and storage cost; it proves the registry artifact, not only a local build output. Measure mismatch rejections, missing rollback digests, platform coverage, and time from test to deployment. A signed statement bound to the wrong digest remains the wrong evidence; identity comparison is the essential step.",
    ["Do not rebuild after final tests and call the new image tested.", "Do not deploy by a mutable tag when the approved record names a digest.", "Do not let an untrusted job certify its own release artifact."],
    ["devops/artifact-promotion", "devops/supply-chain-verification", "devops/untrusted-ci-artifact-handoff", "devops/rollback-image-retention"],
)

lesson(
    "reproducible-build-diff-triage", "Reproducible builds: investigate why equal inputs produce different bytes",
    "Compare two clean builds before treating a digest mismatch as compromise.",
    "A reproducible build emits the same artifact bytes from the same declared inputs and build process. Differences may come from timestamps, filesystem order, environment locale, toolchain version, random identifiers, mutable dependencies, or undeclared files. A mismatch is evidence of uncontrolled input; it is not by itself proof of malicious modification. The investigation must preserve both outputs and the input manifest so the first differing layer can be located.",
    "Build the receipt package twice in separate clean runners using the same source revision, lockfiles, toolchain image digest, and dependency repository snapshot. The fragment fixes the source timestamp input for tools that honor it and records a package digest; it is a diagnostic scaffold, not a claim that the package will now be bit-for-bit identical. Compare archive member names, ordering, modes, timestamps, generated source, and dependency bytes before comparing the whole package again. If a generated manifest embeds the wall clock, change it to a source-derived timestamp or move display time to runtime. If compression adds unstable metadata, adjust packaging rather than normalizing a compromised output after the fact. Record each unexplained difference and block promotion when the release policy requires reproducibility. After repair, repeat on a different runner and compare the actual registry artifact, not only local files.",
    "bash", "set -euo pipefail\nexport SOURCE_DATE_EPOCH=\"$(git show -s --format=%ct HEAD)\"\n./ci/build-receipt-package.sh\nsha256sum dist/receipt-api.tar",
    "Two clean builds roughly double build compute and artifact storage for the check. Making a build reproducible can require pinning toolchains and dependency repositories, which adds maintenance work but improves incident analysis. Measure the fraction of builds that match, the first differing file or layer, and time to identify an undeclared input. A digest comparison alone gives a yes-or-no signal; a useful diff report explains what changed and whether it can affect the deployed behavior.",
    ["Do not assume setting one timestamp variable makes every tool reproducible.", "Do not normalize away a binary mismatch before inspecting its cause.", "Do not compare builds whose dependency or toolchain inputs differ."],
    ["devops/supply-chain-verification", "devops/ci-cache-boundaries", "devops/container-image-builds", "devops/tested-artifact-digest-binding"],
)

titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/ci-evidence-integrity-project"
quiz_path = "quizzes/devops-ci-verification-decisions"
titles[project_path] = "Project: prove a receipt release passed the checks that matter"
titles[quiz_path] = "DevOps CI verification decisions"
unknown = {path for item in specs for path in item["related"] if path not in titles}
assert not unknown, unknown


def links(paths):
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in paths
    ) + "</ul>"


for heading, summary, slugs in [
    ("Candidate and impact gates", "Test the merged revision and fall back when selective coverage is uncertain.", ["merge-queue-candidate-verification", "selective-ci-test-fallback"]),
    ("Reliable test evidence", "Keep flaky tests visible and isolate mutable data per run.", ["flaky-test-quarantine-contract", "ci-test-data-isolation"]),
    ("Declared inputs and complete platforms", "Control test dependencies and require every supported matrix row.", ["hermetic-ci-dependency-boundary", "ci-matrix-required-gate"]),
    ("Artifact bytes and repeatability", "Bind tests to the deployed digest and investigate unequal builds.", ["tested-artifact-digest-binding", "reproducible-build-diff-triage"]),
]:
    paths = ["devops/" + slug for slug in slugs]
    by_path[course]["data"]["modules"].append({"title": heading, "summary": summary, "lessons": paths})
    by_path[course]["body"] += f"<h2>{html.escape(heading)}</h2><p>{html.escape(summary)}</p>" + links(paths)
by_path[course]["updated_at"] = stamp

for index, item in enumerate(specs):
    path = item["path"]
    row = copy.deepcopy(by_path["devops/continuous-integration"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
               title=item["title"], summary=item["summary"], subject="devops",
               category="DevOps", difficulty="Advanced", tags=["devops", "operations"],
               sort_order=20800 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"kind": "tutorial", "reading_minutes": 6,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": course, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in item["related"]]}
    row["body"] = (
        f"<p>{html.escape(item['definition'])}</p><h2>Operational decision</h2>"
        f"<p>{html.escape(item['operation'])}</p>"
        f'<pre><code class="language-{item["language"]}">{html.escape(item["sample"])}</code></pre>'
        f"<h2>Cost and verification</h2><p>{html.escape(item['cost'])}</p>"
        + "<h3>Common Mistakes</h3><ul>"
        + "".join(f"<li>{html.escape(mistake)}</li>" for mistake in item["mistakes"])
        + "</ul><h2>Connected lessons</h2>" + links([course, *item["related"]])
    )
    rows.append(row)

project_related = [item["path"] for item in specs]
project = copy.deepcopy(by_path["devops/practice-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)),
               path=project_path, title=titles[project_path],
               summary="Exercise merge candidates, test selection, flaky checks, isolation, matrices, and digest identity.",
               difficulty="Advanced", sort_order=20890,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 9,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in project_related]}
project["body"] = (
    "<p>Use an isolated receipt repository with a payout dependency, two supported build targets, a disposable database, and a test registry. Configure a protected branch and merge queue in that test repository. Preserve the candidate revision, selected checks, runner identity, service image digest, test report, and deployment selection for every experiment. The drill should fail when evidence is missing, not merely when code has a syntax error.</p>"
    "<h2>Break the gate deliberately</h2><p>Make two pull requests pass alone but fail as a combined dependency change; prove the merge-group check rejects their candidate. Edit a shared schema and show that the selective selector runs the full suite. Remove the base revision from a shallow checkout and verify the same safe fallback. Introduce a parallel test-data collision, then isolate database, queue, cache, and object scopes by run. Reproduce one intermittent failure, place only that test in a time-bounded nonblocking lane, and retain a blocking settlement smoke check. Simulate a skipped required workflow and a canceled architecture row; neither may count as a completed release gate.</p>"
    "<pre><code class=\"language-text\">Receipt release evidence gates\nMerge candidate: checked revision equals accepted revision\nSelection: shared change and unknown base run full suite\nQuarantine: named test, owner, expiry, replacement coverage\nIsolation: two parallel runs share no mutable records\nInputs: clean runner and declared service versions\nMatrix: all supported rows completed and passed\nArtifact: tested digest equals promoted digest\nRebuild: differences explained before reproducibility claim</code></pre>"
    "<h2>Bind checks to release bytes</h2><p>Build and push one image, pull it by digest for final tests, then submit the same digest to a simulated deployment gate. Retag the repository between test and promotion; the gate must still choose the approved digest. Build the package twice from clean runners with fixed inputs and compare both whole-file digests and first differing archive member. Do not declare a mismatch hostile without investigation, and do not declare two matching packages safe without knowing who produced them. Keep the evidence tied to the exact revision and builder.</p>"
    "<h2>Cost and verification</h2><p>Record queue delay, full-suite fallback frequency, quarantine age, orphaned test scopes, cold-run time, matrix runner minutes, and registry storage through rollback. The project passes only when a bad combined commit, missing supported row, or changed image digest blocks promotion. A dashboard showing green from one earlier pull-request head is insufficient.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not convert a skipped workflow into a passing gate.</li><li>Do not rerun a flaky suite until it becomes green and discard the first failure.</li><li>Do not rebuild the image after final tests.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*project_related, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>CI evidence integrity drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("What revision must a merge queue verify?", ["Its combined candidate revision", "Only each pull-request head", "The last release tag"], "The candidate can fail even when individual heads pass."),
    ("What should selective CI do when its base revision is unavailable?", ["Run the complete suite", "Mark checks passed", "Skip every test"], "Uncertain impact requires the safe fallback."),
    ("Why keep a quarantined test running?", ["Its failure signal and repair evidence remain visible", "It becomes permanently optional", "It proves the code is correct"], "Quarantine is a bounded coverage exception."),
    ("What should identify a parallel integration test's mutable records?", ["A unique run scope across all external systems", "A shared customer ID", "Only the runner hostname"], "Isolation must cover database, queue, cache, and objects."),
    ("What makes a containerized test non-hermetic?", ["It still reads an undeclared external service", "It uses an image", "It has a temporary directory"], "A container does not declare every input automatically."),
    ("How should a required platform row that was canceled be treated?", ["As incomplete, not passed", "As green if another row passed", "As experimental by default"], "Every supported row needs a completed result."),
    ("What does disabling matrix fail-fast provide?", ["More diagnostic results after one row fails", "Automatic release approval", "No runner cost"], "Other rows can finish and reveal their own status."),
    ("Which image should reach production after final tests?", ["The same immutable digest tested", "Any image with the same mutable tag", "A rebuilt image from the same source"], "Digest identity connects verification to deployed bytes."),
    ("What should a tag update after testing change?", ["Nothing about the approved deployment digest", "The tested artifact bytes", "The accepted source revision"], "Promotion selects the recorded digest, not a moving tag."),
    ("What does a reproducible-build mismatch establish first?", ["An uncontrolled input or output difference needs investigation", "Malice is proven", "The second build is safe"], "A mismatch is a diagnostic signal."),
    ("Why is SOURCE_DATE_EPOCH alone insufficient?", ["Other tools and inputs can still vary", "It changes the Git commit", "It signs the package"], "Time is only one source of nondeterminism."),
    ("What proves the CI gate corresponds to the released artifact?", ["Candidate revision, test subject digest, and promoted digest agree", "A green badge from last week", "A successful build of unrelated source"], "The evidence chain must name the same revision and bytes."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on test completeness and release artifact identity.",
            sort_order=20900, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in project_related],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Decide whether the actual merge candidate, complete supported matrix, isolated tests, and promoted artifact have enough evidence to release. A green job from a different revision or digest does not answer that question.</p>"
    "<h2>Review these lessons</h2>" + links(project_related)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-network-path-decisions", "quizzes/devops-terraform-ownership-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not count an absent check as a pass.</li><li>Do not deploy a rebuilt image after testing a different digest.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>CI verification check</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": path, "title": titles[path]} for path in [project_path, quiz_path])

for source, targets in {
    "devops/continuous-integration": ["devops/merge-queue-candidate-verification", "devops/selective-ci-test-fallback", "devops/flaky-test-quarantine-contract"],
    "devops/git-change-control": ["devops/merge-queue-candidate-verification"],
    "devops/ci-cache-boundaries": ["devops/hermetic-ci-dependency-boundary", "devops/reproducible-build-diff-triage"],
    "devops/ephemeral-environment-controls": ["devops/ci-test-data-isolation"],
    "devops/multiarch-image-promotion": ["devops/ci-matrix-required-gate"],
    "devops/artifact-promotion": ["devops/tested-artifact-digest-binding"],
    "devops/supply-chain-verification": ["devops/reproducible-build-diff-triage", "devops/tested-artifact-digest-binding"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Advanced follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1, "total_records": len(rows)}))
