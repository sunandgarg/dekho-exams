"""Add software supply-chain evidence contracts to the local DevOps preview."""

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
    "sbom-build-runtime-scope",
    "SBOM scope: distinguish build inputs from shipped components",
    "A software bill of materials is an inventory claim about a defined artifact and generation step.",
    "A dependency lockfile, source-tree scan, and final-image scan answer different questions. The lockfile can include development packages that never ship; a final container can contain operating-system packages, copied binaries, and layers absent from the language lockfile. A useful SBOM states its subject, generation point, components, dependency relationships where known, and gaps. A package list with no relation to a deployable digest cannot settle which production release contains a vulnerable component.",
    "A payment-reconciliation worker is built in two stages. Generate one dependency view from the locked application build and another from the final runtime image. Record the image digest, architecture, generator version, scan mode, and time for each view. Compare the two inventories: flag runtime packages missing from the lockfile view, build-only compilers that should not appear in the final image, and copied binaries whose package origin the scanner cannot identify. Run the process in a disposable container and inspect loaded modules to test whether the scanner missed a statically linked component. Keep unknown entries as unknown; inventing a package version to make coverage appear complete makes later advisory matching worse. For a multi-architecture release, inspect each platform manifest because its base packages may differ. Store the accepted inventories with the release digest and regenerate them when the image is rebuilt, even if application source did not change. Do not publish internal repository credentials or private download paths through SBOM metadata. The inventory is operational evidence, not a guarantee that no other code is present.",
    "text",
    "Payment worker inventory contract\nSubject: final image digest and platform\nSources: lockfile view plus final-image view\nGenerator: version and scan mode recorded\nRelationships: direct and transitive edges where known\nUnknowns: copied binary and unidentified packages reported\nAcceptance: runtime image matches recorded subject digest",
    "Scanning B bytes and P package records costs at least O(B + P) work for a full image pass; graph storage grows with components and dependency edges. More complete scans add pipeline time and artifact storage, but missing runtime packages make incident triage slower. Measure runtime-component coverage, unidentified bytes, stale inventories, and differences between platform variants. A smaller SBOM is not necessarily better if it silently omits the shipped base layer.",
    ["Do not present a lockfile inventory as the entire final image.", "Do not attach one platform's SBOM to every architecture in an image index.", "Do not turn unknown package identities into guessed versions."],
    ["devops/container-image-builds", "devops/multiarch-image-promotion", "devops/hermetic-ci-dependency-boundary", "devops/dependency-patch-campaign"],
)

lesson(
    "sbom-artifact-digest-binding",
    "SBOM binding: keep the inventory attached to the tested digest",
    "An accurate inventory for the wrong artifact is unusable release evidence.",
    "A build can produce an image, tests can run against it, and a later job can generate an SBOM from a mutable tag that has already moved. The resulting document may parse correctly while describing different bytes. Bind the inventory subject to the immutable image digest, verify that digest again at promotion, and require the inventory to be retrievable in the destination registry or evidence store. An inventory is a claim about a subject, not a replacement for verifying the subject itself.",
    "A document-export service builds one image and records its manifest digest. The verification job runs tests against that digest, creates an SBOM from the same digest, and stores a signed mapping of tested digest, SBOM digest, build run, and source revision. A promotion job copies the image by digest into a production registry, resolves the destination digest, and checks it against the tested subject before copying the SBOM. If registry conversion changes the manifest digest while preserving layers, treat that as a new subject requiring an explicit equivalence review; do not silently relabel the old document. Attempt a race in a disposable registry: move the release tag after tests but before inventory generation, then show that digest-based retrieval still selects the tested artifact. Delete the tag and confirm the SBOM remains retrievable by its subject digest. Keep promotion results in an append-only release record so a future incident can identify both the deployed image and the inventory version used for its risk decision. For a multi-platform index, record whether the document covers the index or a particular child manifest.",
    "text",
    "Document-export release binding\nTest subject: immutable image digest\nSBOM subject: same digest and platform scope\nSBOM artifact: own digest and generation run\nPromotion: destination manifest digest verified\nDeployment: digest recorded from workload specification\nRace test: mutable release tag moved after tests",
    "Verification is a small number of digest lookups plus any image scan needed to produce the inventory; scanning the same image repeatedly can dominate pipeline time. Retaining an SBOM for each release adds storage proportional to release count and inventory size. Measure releases without a subject-matched inventory, promotion mismatches, and time to retrieve historical evidence. The strongest scanner result does not help if deployment points at a different digest.",
    ["Do not generate an SBOM from a tag after testing a digest.", "Do not assume a registry copy preserved the manifest digest without checking.", "Do not lose the inventory when the human-readable tag is cleaned up."],
    ["devops/tested-artifact-digest-binding", "devops/registry-tag-mutation-race", "devops/artifact-promotion", "devops/oci-referrer-retention"],
)

lesson(
    "package-identity-advisory-matching",
    "Package identity: verify advisory matches before changing a release",
    "A vulnerability alert depends on mapping an advisory to the exact component present in a specific artifact.",
    "A package name without ecosystem, version, distribution, and build context is often ambiguous. The same-looking library name may refer to different registries or patched distribution packages; a scanner can also miss a vendored copy because its metadata was stripped. Advisory matching should preserve the package's native identifier and the path by which it entered the release. Scanner output is a starting hypothesis, not the final affected-product decision.",
    "A checkout image contains application libraries, a distribution-provided TLS library, and one copied command-line helper. A newly announced vulnerability matches the TLS library name. Record the deployed image digest and SBOM component identifier, then inspect package origin, distribution release, vendor backport status, build flags, and whether the vulnerable code is present in the runtime image. Compare the advisory's affected range with the package's actual source and patch lineage; do not assume that a lower upstream version string means an unpatched distribution build. For the copied helper, obtain its release metadata or rebuild it from a known source because an unidentified binary cannot be cleared by matching only the package manager database. Trace dependency edges to find every service that ships the component, including platform-specific images and old rollback digests. Assign each affected digest an owner and status. If no fix exists, document the reachable attack path and temporary control, then set a review time rather than leaving an alert suppressed forever. Verify the replacement image with the same user-path test used for release acceptance.",
    "text",
    "Checkout advisory triage record\nAdvisory: identifier and affected-version criteria\nComponent: ecosystem, package identity, origin, installed build\nArtifact: image digest and platform\nEvidence: patch lineage, code presence, reachable path\nDisposition: affected, not affected, fixed, or investigating\nOwner: service team with next review time",
    "Matching N inventory components against A advisories can be indexed by ecosystem and package identity rather than scanning every pair, but ambiguous or vendored components still require manual work. Measure unclassified components, affected deployed digests, time from advisory to disposition, and false-positive reversal rate. Prioritize actual exposure and recoverability alongside severity; a release that removes a finding but breaks checkout still needs a safer rollout plan.",
    ["Do not use a bare package name as unique identity.", "Do not infer patch state solely from upstream version numbers.", "Do not close a copied binary finding using only package-manager records."],
    ["devops/sbom-build-runtime-scope", "devops/dependency-patch-campaign", "devops/rollback-image-retention", "devops/release-evidence-record"],
)

lesson(
    "vex-assertion-review-window",
    "VEX decisions: bind a not-affected claim to evidence and expiry",
    "A vulnerability-exploitability statement records an assessment for a named product and vulnerability, not a blanket exception for every future build.",
    "A not-affected disposition needs a reason that can be reviewed: for example, the component is absent, the vulnerable code was excluded, or the code cannot be reached in the deployed product. The assertion must identify the product version or digest and the vulnerability. Rebuilding the image, changing configuration, or learning of a new attack path can invalidate the reasoning even when the package name stays the same.",
    "A claims parser includes a library flagged for a parsing flaw, but the shipped binary excludes the affected module. The owner records the exact image digest, build flags, code-path evidence, vulnerability identifier, status, justification, and reviewer. A second reviewer checks the final runtime image and a test that would fail if the excluded module were enabled. The policy permits a not-affected disposition for that digest only, with a planned revisit after the next rebuild or advisory update. Build a second image that enables the module; its scan must not inherit the first image's suppression. If evidence is inconclusive, use an investigating state and a bounded release decision rather than fabricating a not-affected reason. If the product is affected, record mitigation and patch work separately. Keep the assessment alongside the SBOM and release digest so downstream scanners can read it without mistaking it for the scanner's own finding. Limit who may issue these statements and audit changes; an unsigned text note in a ticket should not silently disable a deployment gate.",
    "text",
    "Claims parser exploitability record\nProduct: exact image digest and architecture\nVulnerability: identifier and affected component\nStatus: not affected\nReason: vulnerable module absent from shipped binary\nEvidence: build flags, binary inspection, regression test\nReview trigger: new digest, config change, advisory update\nApproval: named owner and independent reviewer",
    "A disposition review is O(1) per finding only when evidence is already linked; across F findings, review effort grows with F and with the number of distinct product digests. Narrow statements cost more to maintain but prevent old suppressions from hiding new risk. Measure stale assertions, findings reopened after rebuild, unsupported not-affected claims, and time to revisit an investigating state. A VEX record changes triage, not the underlying shipped bytes.",
    ["Do not apply one not-affected claim to every future image tag.", "Do not suppress a finding without a product identity and testable reason.", "Do not leave investigating status without an owner and review date."],
    ["devops/package-identity-advisory-matching", "devops/sbom-artifact-digest-binding", "devops/policy-exception-expiry", "devops/dependency-patch-campaign"],
)

lesson(
    "build-provenance-builder-trust",
    "Build provenance: verify who asserted how the artifact was made",
    "Build provenance is an attested claim connecting output bytes to a build process and its inputs.",
    "A provenance document may name source revision, build definition, parameters, builder identity, invocation, and subject digest. Those fields are useful only within the trust boundary of the builder that produced the statement. A tenant-controlled job can echo arbitrary metadata, while a protected build service can attest facts observed by its control plane. The release policy must distinguish those assertions rather than treating every well-formed document as equivalent.",
    "A settlement service uses a protected release workflow. The release record requires the artifact digest as subject, an allowed builder identity, the approved repository and revision, and a build definition matching the reviewed workflow. The verifier checks the attestation signature or trusted envelope and compares the subject digest with the image that passed tests. Change the repository URL field inside a copied document; signature verification should fail. Create a valid attestation from a disposable but unapproved workflow; cryptography may pass, but policy should reject its builder identity. Then run the approved workflow with a modified external parameter that selects a debug dependency source; the policy must either reject that parameter or record an explicit review. If the build uses a mutable base tag, provenance alone may not identify the exact base bytes; pin or record resolved digests. Preserve the builder's trust configuration and workflow revision for later incident analysis. Do not place signing credentials inside an untrusted build step merely to obtain an attestation; that allows the step to sign a claim about different bytes.",
    "text",
    "Settlement release provenance gate\nSubject: tested image digest\nBuilder: approved protected release identity\nSource: repository and immutable revision\nDefinition: reviewed workflow identity and parameters\nInputs: resolved base and dependency digests\nNegative tests: altered statement and unapproved builder",
    "Checking an attestation is small compared with rebuilding the image, but verification must fetch and evaluate every required statement for the subject. For R releases, evidence retention grows with R and with the size of recorded inputs. Measure releases with missing or rejected provenance, unapproved builder attempts, and time to reconstruct a prior build's inputs. A signature proves who signed the claim, not that the signer had an appropriate build boundary.",
    ["Do not accept provenance only because its syntax parses.", "Do not equate a valid signature with an approved builder.", "Do not leave mutable input references unresolved in a release record."],
    ["devops/supply-chain-verification", "devops/untrusted-ci-artifact-handoff", "devops/reproducible-build-diff-triage", "devops/tested-artifact-digest-binding"],
)

lesson(
    "attestation-admission-subject-policy",
    "Admission verification: compare the running image with approved evidence",
    "An admission gate must evaluate the image digest the cluster will pull, not a nearby tag or unrelated attestation.",
    "A signature or attestation can be attached to an image digest, but a workload may specify a mutable tag, a multi-platform index, or an image rewritten by an admission mutator. The verifier must define which resolved subject it checks and which builder, repository, and evidence predicates it accepts. Admission is also an availability dependency: verifier timeout, registry outage, and stale trust material can stop new workloads if failure behavior is not rehearsed.",
    "A parcel API is deployed to a test cluster by digest. Configure a verification policy that accepts only the reviewed builder and provenance subject for the exact image being admitted. Test a signed image from an unapproved workflow, a valid statement attached to a different digest, a missing SBOM, and a moved tag; each must receive the intended result. For an image index, verify the index and required platform child manifests according to the policy's declared scope. Run the verifier in audit or warning mode against current workloads before enforcing denial, then measure latency and false denials. Simulate a registry timeout and a verifier outage to choose a failure policy consistent with the service's recovery objective; document a narrow emergency path with an expiry and audit record. A policy that rejects all replacement Pods during a verifier outage can turn a single dependency fault into a service outage. Conversely, silently allowing every image on timeout removes the security boundary. Capture the final admitted image reference and runtime image ID after the Pod starts to detect resolution or mutation differences.",
    "text",
    "Parcel admission matrix\nApproved digest and builder: allow\nUnapproved builder with valid signature: deny\nStatement for another digest: deny\nRequired SBOM missing: deny or reviewed exception\nRegistry or verifier timeout: tested failure behavior\nRuntime image ID: matches admitted subject",
    "Verification adds registry lookups, signature work, and admission latency to each relevant workload creation. Cache by immutable digest with bounded freshness rather than by tag; a cache keyed only by name can reuse a verdict after the tag moves. Measure p95 admission latency, timeout rate, false denials, bypass use, and Pods whose runtime digest differs from the reviewed subject. Security policy and recovery availability must be tested together.",
    ["Do not verify a tag once and assume it remains on the same bytes.", "Do not accept a valid attestation for a different subject digest.", "Do not enforce a gate before testing verifier and registry outages."],
    ["devops/admission-policy-guardrails", "devops/admission-webhook-outage", "devops/build-provenance-builder-trust", "devops/signature-trust-rollover"],
)

lesson(
    "base-image-rebuild-trigger",
    "Base-image refresh: rebuild and retest when inherited bytes change",
    "An application source revision can remain fixed while its inherited runtime packages become obsolete.",
    "A container base tag is a pointer, not a guarantee that the same digest will resolve next week. Security fixes may arrive through distribution rebuilds without a change to application dependencies. Conversely, rebuilding from a mutable tag without recording its resolved digest can produce different output that cannot be explained from source commit alone. Base refresh is a new release with its own tests, SBOM, provenance, and rollback plan.",
    "A receipt API inherits a minimal runtime image. Record the base manifest digest used for each architecture at build time and compare it with the approved update candidate. Trigger a rebuild when a base package needs a fix or the base image's support window changes; do not wait for an application code commit. Regenerate the final-image SBOM and compare the component graph, file changes, image size, startup behavior, and runtime identity. Test the release against synthetic receipt traffic and one node restart in each target architecture before canary promotion. Keep the previous digest pullable during rollback, but do not let an old vulnerable rollback image remain an unreviewed default for months. If the new base changes libc, certificate roots, locale files, or user IDs, verify behavior under actual deployment restrictions rather than relying on unit tests. Record advisory disposition for old and new digests. Pin the new base by digest for the tested build; schedule a later review rather than relying on automatic tag motion. A successful scanner report with no critical finding does not prove the application starts or can reach its dependencies.",
    "text",
    "Receipt API base refresh\nOld base digest: recorded per architecture\nCandidate base digest: reviewed before build\nNew image: fresh SBOM, provenance, test result\nRuntime checks: startup, TLS, filesystem, user ID\nCanary: receipt success and tail latency\nRollback: old digest pullable for a bounded window",
    "A rebuild costs CPU, network transfer, scan time, and canary capacity even when application code is unchanged. For A architectures and T runtime checks, the acceptance matrix grows with A × T, while SBOM comparison scales with component count. Measure age of deployed base digests, rebuild lead time after an advisory, canary failures caused by base changes, and rollback-window exposure. Treat inherited package fixes as delivery work, not just a registry housekeeping task.",
    ["Do not assume an unchanged source commit means unchanged runtime risk.", "Do not rebuild from a moving tag without recording the resolved base digest.", "Do not delete the old image before the tested rollback window ends."],
    ["devops/container-image-builds", "devops/dependency-patch-campaign", "devops/multiarch-image-promotion", "devops/rollback-image-retention"],
)

lesson(
    "oci-referrer-retention",
    "Registry evidence retention: keep referrers with the release digest",
    "An image and the statements attached to it can have separate registry objects and cleanup behavior.",
    "An OCI registry can expose artifacts that refer to an image digest, including SBOMs and attestations. The reference relationship lets clients discover evidence for a subject, but a registry copy or retention rule may omit or delete those attached objects. Deleting a tag can be different from deleting the underlying manifest; implementations also vary in supported deletion operations. The release owner must test evidence discovery and pullability in the registry used for deployment and rollback.",
    "A billing service promotes an image from a build registry to a production registry. The source digest has a signed provenance statement and a final-image SBOM. Copy the image by digest, then enumerate evidence that refers to the destination subject. Copy each required statement, verify its own digest and signature, and reject promotion if the expected set is missing or points at the wrong subject. Repeat this on a registry that uses an alternate referrer-discovery mechanism, because a client returning no referrers is not necessarily proof none exist. Apply a dry-run retention rule that protects running, canary, rollback, and incident-held digests along with their required evidence. In a disposable repository, delete an unused tag and verify the protected digest and evidence remain pullable; then test manifest deletion behavior separately. Record which artifacts are held for legal or operational reasons and which can expire after the review window. During registry failover, verify a clean node can pull the image and a clean verifier can fetch its evidence from the replica. A cached success from the source registry is not acceptable proof of destination availability.",
    "text",
    "Billing registry promotion contract\nSubject: tested image digest\nEvidence: SBOM digest and provenance digest\nDestination: image and required referrers discoverable\nRetention: running, canary, rollback, incident hold protected\nClean-node test: image pull and evidence verification\nDeletion test: tag removal distinguished from manifest removal",
    "For R retained release digests and E attached evidence objects, inventory and retention review process O(R + E) records; copy cost includes bytes for both images and evidence. Keeping every historical artifact indefinitely raises storage charges, while deleting the only attestation can make a valid rollback inadmissible. Measure evidence discovery failures, orphaned statements, protected digest age, and successful clean-node failover pulls. A release is retained only when its bytes and required proof both remain available.",
    ["Do not assume image copy also copied its SBOM and attestation.", "Do not treat deleting a tag as equivalent to deleting its digest everywhere.", "Do not test registry failover only from a node with cached layers and trust data."],
    ["devops/registry-replica-promotion", "devops/rollback-image-retention", "devops/sbom-artifact-digest-binding", "devops/attestation-admission-subject-policy"],
)

titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/supply-evidence-promotion-project"
quiz_path = "quizzes/devops-supply-evidence-decisions"
titles[project_path] = "Project: promote an image with verifiable supply-chain evidence"
titles[quiz_path] = "DevOps supply-chain evidence decisions"
assert all(path in titles for item in specs for path in item["related"])


def links(paths):
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in dict.fromkeys(paths)
    ) + "</ul>"


for heading, summary, slugs in [
    ("Inventory scope and identity", "Describe shipped components and bind the inventory to immutable release bytes.", ["sbom-build-runtime-scope", "sbom-artifact-digest-binding"]),
    ("Advisory and exploitability decisions", "Match advisories to actual components and keep not-affected claims reviewable.", ["package-identity-advisory-matching", "vex-assertion-review-window"]),
    ("Build claims and admission", "Approve the builder and exact subject before a workload starts.", ["build-provenance-builder-trust", "attestation-admission-subject-policy"]),
    ("Refresh and retention", "Rebuild inherited packages and preserve evidence through registry cleanup.", ["base-image-rebuild-trigger", "oci-referrer-retention"]),
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
               category="DevOps", difficulty="Advanced", tags=["devops", "supply-chain"],
               sort_order=22200 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
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
               summary="Bind SBOM, advisory decisions, provenance, and registry evidence to one tested image digest.",
               difficulty="Advanced", sort_order=22290,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 9,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in project_related]}
project["body"] = (
    "<p>Use a disposable source registry, a separate destination registry, a protected build workflow, and a test cluster. Build a synthetic settlement worker for two architectures. Record the immutable image index digest and child-manifest digests before testing. The exercise is accepted only if the running image, final-image inventories, provenance, vulnerability disposition, and retained registry evidence can be joined to the approved release bytes without relying on a mutable tag.</p>"
    "<h2>Inventory the shipped artifact</h2><p>Produce a lockfile inventory and final-image inventories for both architectures. Compare application packages, operating-system packages, copied binaries, dependency edges, and unknown components. Give each document a subject digest and generator record. Move a release tag after tests; the inventory job must still read the tested digest. Verify each SBOM remains retrievable after tag cleanup. Introduce a second platform variant with a changed base package and prove that the first variant's inventory does not silently stand in for both.</p>"
    "<h2>Triage and document one finding</h2><p>Inject a synthetic vulnerable-component alert. Match it to ecosystem, package origin, distribution build, and the deployed digest. Create one affected disposition with remediation work and one not-affected disposition with a testable reason tied to an exact digest. Rebuild the image with a different module set and show that the old not-affected statement is not automatically inherited. Keep the reviewer, evidence, and revisit trigger in the release record. If component identity is unknown, leave it unresolved and assign investigation rather than forcing a false match.</p>"
    "<pre><code class=\"language-text\">Supply evidence acceptance\nImage index and platform digests recorded before tests\nEach runtime SBOM names its actual subject and unknowns\nAdvisory disposition names component and release digest\nNot-affected claim has evidence and rebuild trigger\nProvenance signer and builder are both approved\nAdmission verifies the exact subject the cluster pulls\nDestination registry exposes image and required referrers\nRollback digest and evidence survive cleanup dry-run</code></pre>"
    "<h2>Verify builder and admission</h2><p>Generate provenance in the protected release workflow. Test a copied statement with an altered source field, a properly signed statement from an unapproved workflow, and a statement for another image digest. Admission should reject the wrong builder or subject even when the document parses. Turn the verifier into audit mode first, measure timing and false denials, then test enforced behavior against a canary Deployment. Simulate registry and verifier outages and record the chosen failure path. Compare the admitted reference with the runtime image ID after Pod start.</p>"
    "<h2>Promote and retain proof</h2><p>Refresh the base image without changing application source, then rebuild, scan, and retest. Copy the selected image to the destination by digest and enumerate its attached evidence there; do not infer a copy from source-side discovery. Run a cleanup dry-run protecting current, canary, rollback, and incident-held digests with their required evidence. Delete an unused tag in the disposable registry and verify the retained subject remains pullable from a clean node. Report scan time, admission latency, missing referrers, stale dispositions, registry bytes, and rollback pull time. Mark provider- or registry-specific behavior unverified when the disposable environment cannot reproduce it.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not equate a valid SBOM file with an inventory of the deployed bytes.</li><li>Do not let a finding exception follow a mutable tag across rebuilds.</li><li>Do not clean up the only evidence needed to admit a rollback image.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*project_related, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Supply evidence promotion drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("Why scan the final runtime image as well as a lockfile?", ["The image may contain base packages and copied binaries absent from the lockfile", "The lockfile always changes the image tag", "Only the image scan runs tests"], "The two inventories have different scopes."),
    ("What must identify an SBOM's release subject?", ["The immutable artifact digest and relevant platform scope", "Only a movable tag", "Only the repository display name"], "The document must describe the bytes actually promoted."),
    ("What should happen if a registry copy changes the manifest digest?", ["Review equivalence and bind evidence to the destination subject", "Assume the old statement applies", "Delete the source image"], "A changed digest is a new subject for verification."),
    ("What distinguishes similarly named packages during advisory matching?", ["Ecosystem, origin, installed build, and artifact digest", "Only a display name", "Only the scanner color"], "Identity and patch lineage affect the conclusion."),
    ("How far should a not-affected assertion apply?", ["To the reviewed product identity and vulnerability with a revisit trigger", "To every future tag", "To all packages in the registry"], "A rebuild can change the code path or shipped bytes."),
    ("What should an inconclusive exploitability review record?", ["Investigating status with owner and bounded decision", "A guessed not-affected reason", "No record"], "Unknown risk needs an explicit follow-up."),
    ("What does a provenance signature establish by itself?", ["Who signed the claim, not whether the builder was approved", "That every dependency is safe", "That the image runs in production"], "Builder policy and subject checks are separate."),
    ("What must admission compare with an attestation?", ["The exact digest the cluster will pull", "Only the human-readable tag", "Only the release ticket title"], "Evidence for another subject cannot authorize this image."),
    ("Why test verifier failure behavior?", ["An outage can block replacements or silently bypass the gate", "It reduces image size", "It changes the SBOM format"], "Admission affects both security and recovery availability."),
    ("Why can a base-image fix require a new release?", ["Inherited runtime bytes changed and need tests and new evidence", "Application source must have changed", "A tag is always immutable"], "Base refresh changes the deployable artifact."),
    ("Does copying an image guarantee attached statements moved too?", ["No, enumerate and verify destination evidence", "Yes, every registry does", "Only after deleting a tag"], "Image and referrer objects have separate transfer behavior."),
    ("What must a rollback retention rule protect?", ["The digest and evidence needed for pull and admission", "Only the release tag name", "Only the current scanner report"], "A rollback is unusable without both bytes and required proof."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on inventories, advisories, provenance, admission, and registry retention.",
            sort_order=22300, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in project_related],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Decide whether the inventory, advisory disposition, provenance, and admission result refer to the same release bytes. A signed statement or clean scan is insufficient when its subject changed during promotion.</p>"
    "<h2>Review these lessons</h2>" + links(project_related)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-cloud-authorization-decisions", "quizzes/devops-artifact-trust-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not bind release evidence to a mutable tag.</li><li>Do not assume destination registries retain source-side referrers.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Supply evidence check</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": path, "title": titles[path]} for path in [project_path, quiz_path])

for source, targets in {
    "devops/supply-chain-verification": ["devops/sbom-build-runtime-scope", "devops/build-provenance-builder-trust"],
    "devops/dependency-patch-campaign": ["devops/package-identity-advisory-matching", "devops/base-image-rebuild-trigger"],
    "devops/tested-artifact-digest-binding": ["devops/sbom-artifact-digest-binding", "devops/attestation-admission-subject-policy"],
    "devops/signature-trust-rollover": ["devops/build-provenance-builder-trust", "devops/attestation-admission-subject-policy"],
    "devops/registry-replica-promotion": ["devops/oci-referrer-retention"],
    "devops/rollback-image-retention": ["devops/oci-referrer-retention", "devops/base-image-rebuild-trigger"],
    "devops/private-package-name-boundary": ["devops/package-identity-advisory-matching"],
    "devops/policy-exception-expiry": ["devops/vex-assertion-review-window"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Supply evidence follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1, "total_records": len(rows)}))
