"""Add artifact trust and registry recovery lessons to the DevOps curriculum."""

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
    "untrusted-ci-artifact-handoff", "Untrusted CI artifacts: separate a pull-request test from promotion",
    "Treat files produced by untrusted code as data until a trusted build creates a release.",
    "A pull-request workflow can execute code supplied by a contributor. Its artifacts are output from that trust level, even if a later privileged workflow downloads them. A file named like a package or test report does not become a trusted release merely by crossing into a protected job. Archive extraction, generated scripts, metadata fields, and path names can each carry hostile input.",
    "A claims-service repository accepts external pull requests. Run their tests with a read-only token, no deployment secrets, and an isolated runner. A protected workflow may read a structured test result, but must validate its schema, size, path, and relation to the reviewed commit; it must never execute a script from the artifact or promote its binary directly. After merge to a protected branch, rebuild from the reviewed commit in a separate trusted job and bind the resulting digest to that source and builder identity. The text contract makes the handoff explicit. Inject an artifact containing a shell script named like a test report and confirm the protected job rejects it without executing it. Try a path-traversal archive and a mismatched commit identifier as separate cases. A green test run from a fork supports review; it is not the source of production bytes.",
    "text", "Claims release handoff\nPull-request job: read-only token, no secrets, disposable runner\nAllowed transfer: bounded JSON test result for reviewed commit\nRejected transfer: executable, archive with unsafe paths, release binary\nProtected branch job: fresh checkout and fresh build\nPromotion key: trusted build digest plus reviewed source revision",
    "A fresh protected build consumes more CI time and compute than directly reusing a pull-request artifact. The cost buys a clear trust boundary. Validation of untrusted results also takes maintenance; keep the accepted schema small. Record the source revision, producing workflow, artifact digest, and promotion decision separately so an operator can distinguish test evidence from release provenance. A privileged workflow that checks out the contributor's branch and runs it recreates the original risk.",
    ["Do not run a downloaded pull-request script in a privileged workflow.", "Do not treat a file name or green badge as proof of release identity.", "Do not let an untrusted archive choose arbitrary extraction paths."],
    ["devops/github-actions-security", "devops/self-hosted-runner-isolation", "devops/supply-chain-verification", "devops/artifact-promotion"],
)

lesson(
    "ci-oidc-claim-boundary", "CI OIDC claims: bind cloud access to the exact deployment job",
    "Constrain issuer, audience, subject, repository, and protected environment.",
    "A short-lived OIDC token removes the need for a stored cloud access key, but it still grants authority according to a trust policy. A broad subject match can let a different branch, workflow, repository, or event assume the same role. The cloud role must verify the token's issuer and intended audience and bind the accepted identity to the deployment boundary actually protected by review.",
    "A payment API has separate preview and production jobs. Give the preview role no production permissions. For production, match the provider's verified subject format for the protected repository and environment, check the intended audience, and limit the role's cloud actions and resources. The policy block is a claim checklist, not a provider-specific trust document; exact claim syntax must be taken from the token format used by the organization's identity provider. Deny a pull-request job, a feature branch, a different repository, and a job with the wrong audience in a disposable account. Then prove the protected production job can assume the role and perform only its required deployment action. Record role session identity with the release, not the bearer token itself. Recheck the trust policy after repository transfer, environment rename, or reusable-workflow changes because these may alter the accepted identity shape. A short token lifetime limits exposure time but cannot repair a wildcard trust rule.",
    "text", "Payment deployment trust contract\nIssuer: approved CI identity provider\nAudience: exact cloud token-exchange audience\nSubject: protected repository and production environment\nAllowed event: protected deployment workflow only\nRole actions: release resources required by payment API\nNegative checks: pull request, feature branch, other repository",
    "Narrow trust adds setup and migration work when workflows or repository identifiers change. Broad trust is cheaper to configure but increases the number of jobs able to deploy. Log successful and denied role assumptions with nonsecret claims and compare them with approved releases. Avoid placing token contents in build logs or test fixtures. A successful role assumption is only the identity gate; artifact digest and deployment target still need separate checks.",
    ["Do not trust any job from a repository when only one protected environment should deploy.", "Do not omit audience validation because the subject looks specific.", "Do not log the bearer token while debugging denied claims."],
    ["devops/github-actions-security", "devops/federated-workload-identity", "devops/release-evidence-record", "devops/untrusted-ci-artifact-handoff"],
)

lesson(
    "container-build-secret-boundary", "Build secrets: keep credentials out of layers and exported caches",
    "Use a temporary secret mount and inspect the resulting artifact, history, and cache.",
    "A build may need a credential to fetch a private dependency. Passing it as a build argument, environment variable, copied file, or command literal can expose it in image metadata, layers, logs, or an exported cache. A dedicated build secret mount makes the value available only to a selected build step, but the command inside that step can still accidentally write the value into its output.",
    "A settlement worker fetches a private module during image creation. Supply the read-only package token to the builder as a temporary secret mount and never copy the token into the build context. The Dockerfile fragment shows the mount shape without including a real credential; pair it with a CI secret source and a locked dependency set. Run the build with a disposable canary token. Search the final image filesystem, image history, provenance fields, build logs, and exported cache for that token. Revoke it after the test and repeat a clean build without cache to prove dependency resolution does not rely on stale credentials. If the fetch command writes an authenticated package URL or token into a config file, remove that file in the same build step and verify it did not enter an exported layer. Keep the runtime stage free of package-manager credentials and build tools.",
    "dockerfile", "FROM python:3.13-slim AS dependency-builder\nWORKDIR /build\nCOPY requirements.lock .\nRUN --mount=type=secret,id=package_token \\\n    PIP_INDEX_URL=\"$(cat /run/secrets/package_token)\" \\\n    pip wheel --no-deps --wheel-dir /wheels -r requirements.lock\nFROM python:3.13-slim\nCOPY --from=dependency-builder /wheels /wheels",
    "A clean builder and secret scanning add CI time. Keeping an external cache improves speed but creates another place to inspect and restrict. A secret mount limits automatic persistence; it does not sanitize the outputs of a command that prints or copies the secret. Rotate any token found in an artifact and rebuild from a clean context after removing the leak. Measure cache hit rate separately from security checks so a faster build is not mistaken for a safer one.",
    ["Do not use a build argument to carry a package credential.", "Do not assume a secret mount prevents the build command from copying the value out.", "Do not verify only the final filesystem while ignoring history, logs, and cache."],
    ["devops/container-image-builds", "devops/ci-cache-boundaries", "devops/secret-rotation-rollout", "devops/supply-chain-verification"],
)

lesson(
    "registry-tag-mutation-race", "Registry tag mutation: reject release decisions based on a moving pointer",
    "Resolve a tag once, then verify and deploy the same digest.",
    "A registry tag names a reference that may point to different image content over time unless its repository enforces immutability. A scanner can inspect one digest while a later deployment pulls another digest through the same tag. Even an immutable tag rule can vary by repository or exception, so the release record should carry the exact image digest that passed checks.",
    "A claims API pipeline scans a candidate tag and waits for approval. At build completion, record the digest returned by the registry. Run tests, provenance verification, and scan against that digest; at approval, compare the deployment manifest's digest to the approved one. The read-only commands inspect one repository's tag configuration and image identity. In a disposable registry, move a mutable candidate tag after scanning and verify the deployment gate refuses the changed digest. Use immutable release tags where the registry supports them, but still pin the production manifest to the digest. When copying across registries, verify the destination object's digest or an explicitly recorded mapping if a conversion changes bytes. Treat a missing destination artifact as a failed promotion rather than falling back to a tag with the same human-readable name.",
    "bash", "aws ecr describe-repositories --repository-names claims-api --query 'repositories[].{name:repositoryName,mutability:imageTagMutability}'\naws ecr describe-images --repository-name claims-api --image-ids imageTag=release-47 --query 'imageDetails[].{digest:imageDigest,tags:imageTags}'",
    "Digest pinning increases release-record precision and may require explicit manifest updates for each build. Mutable tags are convenient for development but create a time-of-check versus time-of-use race. Tag immutability reduces accidental moves, yet a deploy policy still needs to compare the approved digest with the actual image. Monitor unexpected tag changes, pull failures, and running digests by revision. A scan result bound only to a tag is ambiguous after that tag moves.",
    ["Do not scan by tag and deploy by tag after an approval delay.", "Do not assume every registry or repository enforces the same mutability rule.", "Do not accept an identically named destination tag without checking its content identity."],
    ["devops/artifact-promotion", "devops/supply-chain-verification", "devops/multiarch-image-promotion", "devops/release-evidence-record"],
)

lesson(
    "signature-trust-rollover", "Signature trust rollover: rotate verification roots without disabling admission",
    "Stage old and new trust material, then remove the old path after evidence.",
    "An artifact signature is useful only when a verifier accepts the right signer, issuer, trust root, and artifact digest. Rotating a signing key or identity-provider certificate can strand valid releases if admission trusts only the old material; trusting both indefinitely leaves an obsolete authority active. The verification policy, signing job, and deployment admission path must move in a coordinated window.",
    "A payment service moves its build signer to a new identity. First inventory every verifier in CI, admission, and disaster recovery, including offline environments. Add the new trusted identity or root while retaining the old one for a bounded overlap, then sign a disposable image digest with the new path and verify it through each gate. The text contract keeps the transition reviewable. Reject a signature from an unrelated identity and reject a valid signature over a different digest. Promote one new-signed canary, check its running digest, then retire the old signer and remove old trust after all required rollback artifacts have either been re-signed under an approved path or have an explicit exception with expiry. If a signing service is unavailable during a rollout, pause promotion; do not turn verification off globally. Record which verifier accepted each release and how its trust material was distributed.",
    "text", "Payment signer rollover\nPhase 1: inventory CI, admission, and recovery verifiers\nPhase 2: trust old and new identities for a bounded window\nPhase 3: verify new-signed canary digest; reject wrong signer and digest\nPhase 4: move rollback inventory or issue narrow exception\nPhase 5: remove old trust and test old-signer denial",
    "Running two trusted paths temporarily increases the number of credentials that can authorize a release. Removing the old path too soon can make rollback impossible. Each verifier update costs deployment and test time, especially in disconnected clusters. Monitor signature failures by reason rather than only a pass rate. Trust-root updates must be distributed through an authenticated channel; a fetched root from the same untrusted artifact being verified is circular trust.",
    ["Do not disable admission verification when one signer becomes unavailable.", "Do not keep the old signer trusted forever after the migration.", "Do not accept a correct signer attached to the wrong digest."],
    ["devops/supply-chain-verification", "devops/admission-policy-guardrails", "devops/artifact-promotion", "devops/policy-exception-expiry"],
)

lesson(
    "registry-replica-promotion", "Registry replicas: prove the recovery region has the exact release image",
    "Gate failover on replicated digests, credentials, and pull reachability.",
    "Cross-region registry replication is asynchronous in many setups. A rule configured in the source registry does not prove a newly pushed release has arrived in the destination. Repository permissions, lifecycle settings, encryption behavior, and tag rules may differ across registries. A recovery cluster also needs working pull credentials and network access to the destination, not just stored image bytes.",
    "A document parser is deployed in one region and kept ready for regional recovery. For each approved release, record the source digest and every platform-specific child digest if the image is multi-architecture. Query the recovery registry for the expected object and verify its manifest identity before declaring the release recoverable. The sample is read-only and inspects one digest in the destination account. In a disposable recovery cluster, pull that digest with the actual workload identity, start the container on each target architecture, and run a synthetic parse. Check destination repository policy, encryption key access, and retention independently; do not assume source settings replicated. Delay one image copy deliberately and ensure the failover gate blocks promotion to the missing digest. Retain the previous known-good release in both regions until the new one passes the target-cluster test.",
    "bash", "aws ecr describe-images --repository-name document-parser --image-ids imageDigest=sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa --region ap-south-2 --query 'imageDetails[].{digest:imageDigest,tags:imageTags}'",
    "Replication adds registry storage and transfer cost. Holding two known-good releases adds retention cost but makes rollback possible when the newest image is missing or broken. A digest lookup proves registry presence, not that a Pod can authenticate, pull, and run the image. Track replication age, missing digests, pull failures, and synthetic transaction results per region. A fallback to a mutable tag can silently deploy different bytes.",
    ["Do not treat a configured replication rule as proof of an individual digest.", "Do not omit destination pull credentials and network access from a failover test.", "Do not assume repository policies and retention settings follow the image copy."],
    ["devops/multi-region-failover", "devops/object-replication-recovery", "devops/multiarch-image-promotion", "devops/registry-tag-mutation-race"],
)

lesson(
    "rollback-image-retention", "Rollback image retention: keep every approved fallback pullable",
    "Exclude running and rollback digests from registry cleanup until their window ends.",
    "A registry retention rule can delete an image that is no longer tagged even while a deployment manifest still references its digest. Running Pods may keep serving because the image is cached on their nodes, yet a replacement Pod or rollback cannot pull the deleted object. The retention decision must be based on deployed, rollback, and recovery-region references rather than tag age alone.",
    "A settlement API keeps two approved versions for rollback. Before a registry lifecycle change, export the exact digests referenced by live workloads, pending rollouts, and recovery manifests. Compare them with candidate expirations and retain both current and rollback digests in every required region. The text fragment describes the release inventory that a cleanup job must consult; its values are synthetic. Test by replacing one Pod after the old digest would otherwise have expired, and verify it pulls from the registry rather than relying on a node cache. Then execute a rollback in a disposable environment and check a real settlement request. Mark a digest eligible for deletion only after its rollback window closes, no workload or recovery plan references it, and a newer approved fallback is verified. If the registry supports tag-based retention, keep protected tags as a convenience but still compare actual digest references.",
    "text", "Settlement retention gate\nCurrent digest: sha256:47a4...\nRollback digest: sha256:82bd...\nRecovery region: both digests present and pull-tested\nDelete candidate: absent from live, rollout, and rollback manifests\nProof: replacement Pod pulls and synthetic settlement succeeds",
    "Longer retention uses storage and may increase inventory-review time. Overaggressive cleanup reduces spend briefly but can turn a routine restart into an outage. A successful running Pod is weak evidence because its node may have cached layers. Observe registry pull errors, missing digest checks, and rollback drill outcomes. Cleanup should be reversible where possible and should never infer safety from the absence of a human-friendly tag alone.",
    ["Do not delete an untagged image without checking digest references.", "Do not call a cached running Pod proof that the registry can still serve the image.", "Do not expire the prior release before the new one passes recovery-region checks."],
    ["devops/artifact-promotion", "devops/registry-replica-promotion", "devops/progressive-delivery", "devops/release-evidence-record"],
)

lesson(
    "private-package-name-boundary", "Private package names: prevent a public registry winning resolution",
    "Bind internal dependencies to an approved registry and verified lockfile.",
    "A build that searches public and private package indexes may select a public package with the same name as an internal dependency. Some package managers do not prioritize the private index simply because it is listed first. A higher matching version can be chosen from an unintended source, turning an ordinary dependency update into a supply-chain incident. A lockfile helps only if its package identity and source are checked and enforced by the installer.",
    "A receipt processor depends on an internal payment-rule library. Put internal packages in an organization-controlled namespace where the ecosystem supports it, and configure the installer so that the internal name resolves only through the approved repository. The text contract avoids assuming one package manager's syntax is portable to another. In a disposable registry test, publish a higher-version collision under a look-alike public name and confirm the build refuses it. Generate a resolution report from a clean runner and inspect package name, source registry, version, and checksum before release. If a mirror is used, verify it authenticates upstream sources and cannot silently substitute a different artifact for the same lock entry. Do not repair a failed private-registry lookup by enabling every public fallback during an incident; that changes the trust boundary at the moment controls are weakest. Keep package publish rights separate from package read rights.",
    "text", "Receipt dependency resolution contract\nInternal namespace: organization-owned payment packages\nSource: approved private registry or authenticated mirror only\nLock record: exact package, source, version, checksum\nClean-runner check: reject public collision and source mismatch\nPublish permission: separate from build read permission",
    "An isolated private feed and authenticated mirror add hosting, credential, and availability costs. Public fallback can improve availability but may admit an unintended package; decide the source policy before an outage. Check the dependency graph from a clean runner because a warm cache can hide a wrong registry configuration. Monitor package-source changes and new publisher identities as release signals. An exact version alone is not enough when two registries can serve different bytes under the same name.",
    ["Do not assume a listed private index has priority over every public candidate.", "Do not accept a dependency solely because its version matches the lock entry.", "Do not give routine build jobs package-publish authority."],
    ["devops/ci-cache-boundaries", "devops/dependency-patch-campaign", "devops/container-build-secret-boundary", "devops/supply-chain-verification"],
)

titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/artifact-trust-recovery-project"
quiz_path = "quizzes/devops-artifact-trust-decisions"
titles[project_path] = "Project: recover an artifact trust chain"
titles[quiz_path] = "DevOps artifact trust decisions"
for item in specs:
    assert all(path in titles for path in item["related"]), item["path"]


def links(paths):
    return "<ul>" + "".join(f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>' for path in paths) + "</ul>"


for heading, summary, slugs in [
    ("Build identity and private inputs", "Separate untrusted artifacts, deployment claims, build secrets, and package sources.", ["untrusted-ci-artifact-handoff", "ci-oidc-claim-boundary", "container-build-secret-boundary", "private-package-name-boundary"]),
    ("Registry identity and signing trust", "Bind a release to exact bytes and rotate trust without skipping verification.", ["registry-tag-mutation-race", "signature-trust-rollover"]),
    ("Recovery image availability", "Prove exact digests remain pullable in every required region and rollback window.", ["registry-replica-promotion", "rollback-image-retention"]),
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
               sort_order=19600 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"kind": "tutorial", "reading_minutes": 6,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": course, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in item["related"]]}
    row["body"] = (f"<p>{html.escape(item['definition'])}</p><h2>Operational decision</h2>"
                   f"<p>{html.escape(item['operation'])}</p>"
                   f'<pre><code class="language-{item["language"]}">{html.escape(item["sample"])}</code></pre>'
                   f"<h2>Cost and verification</h2><p>{html.escape(item['cost'])}</p>"
                   + "<h3>Common Mistakes</h3><ul>"
                   + "".join(f"<li>{html.escape(mistake)}</li>" for mistake in item["mistakes"])
                   + "</ul><h2>Connected lessons</h2>" + links([course, *item["related"]]))
    rows.append(row)

project_related = [item["path"] for item in specs]
project = copy.deepcopy(by_path["devops/practice-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)),
               path=project_path, title=titles[project_path],
               summary="Prove that an untrusted test cannot replace release bytes and that approved images remain pullable.",
               difficulty="Advanced", sort_order=19690,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 9,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in project_related]}
project["body"] = (
    "<p>Run this drill with disposable repositories, a test registry, synthetic claims data, and a restricted cloud role. Create a protected release job and a separate pull-request test job. Before injecting faults, capture the reviewed commit, trusted build identity, image digest, signing identity, dependency sources, and recovery-region pull result. Use a canary credential that can be revoked after the exercise.</p>"
    "<h2>Cross and reject trust boundaries</h2><p>Produce a malicious test artifact in the untrusted job: give it a report-like name while embedding a script and an unsafe archive path. The protected job may inspect a bounded structured report but must not execute or promote that artifact. Attempt to assume the deployment role from a feature branch, another repository, and a job with the wrong audience; all three must be denied. Build the release from the protected commit using a private package and a temporary secret mount. Publish a public name collision and verify the clean build still resolves the approved private package. Scan the image, cache, logs, and metadata for the canary credential; revoke it after the check.</p>"
    "<pre><code class=\"language-text\">Artifact trust drill gates\nUntrusted artifact: cannot execute or become release binary\nCloud role: only protected deployment job assumes it\nBuild credential: absent from layers, history, cache, and logs\nDependency: source and checksum match approved lock\nPromotion: scanned digest equals deployed digest\nSigner: new identity accepted; wrong identity denied\nRecovery: current and rollback digests pull and run</code></pre>"
    "<h2>Exercise registry and rollback failure</h2><p>Move a mutable test tag after scan approval and confirm the deployment gate rejects the changed digest. Stage a new signing identity alongside the old one, admit a new-signed canary, and deny an unrelated signer. Delay registry replication for one release so the recovery gate blocks failover until the exact digest is present and pull-tested. Mark an old untagged digest for cleanup while a rollback manifest still references it; the retention gate must preserve it. Replace a Pod and perform a rollback in the disposable cluster to prove the registry serves the prior release rather than relying on a node cache.</p>"
    "<h2>Cost and verification</h2><p>Record build minutes, registry storage and transfer, signature verification time, and denied role assumptions. The acceptance record needs one reviewed source revision, one approved digest, a tested signer identity, a clean credential scan, and working current and rollback pulls in the recovery target. A green test badge, source registry rule, or already running Pod is insufficient on its own. Delete only test resources after retaining the evidence.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not reuse an untrusted binary because tests passed.</li><li>Do not verify a tag and deploy a later tag value.</li><li>Do not expire an untagged digest still required for rollback.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*project_related, project_hub]))
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Artifact trust recovery drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("What may a protected job do with a pull-request test artifact?", ["Validate a bounded data report without executing its content", "Promote its binary directly", "Run its scripts with deployment credentials"], "The artifact keeps the trust level of the job that produced it."),
    ("Which build should create production bytes after an external pull request merges?", ["A fresh trusted build from the reviewed protected commit", "The external pull-request build", "Any file with a release-like name"], "The release must bind reviewed source to a trusted builder."),
    ("What does a narrow CI OIDC trust policy check?", ["Issuer, audience, and the authorized job identity", "Only that the token is short-lived", "Only the container tag"], "Short lifetime does not narrow who can assume the role."),
    ("Why is a build argument a poor place for a package token?", ["It can appear in build metadata or history", "It prevents dependency resolution", "It automatically revokes the token"], "Build variables are not a secret transport."),
    ("What still needs inspection after using a secret mount?", ["Image, logs, metadata, and exported cache for a copied value", "Only the mount path name", "Only the repository tag"], "The build command can leak the mounted value into outputs."),
    ("Why can scan-by-tag followed by deploy-by-tag be unsafe?", ["The tag can point to different bytes between checks", "A digest changes whenever it is read", "A scan always deletes the tag"], "The release check must bind to one digest."),
    ("What should a signer rollover test reject?", ["Wrong signer and valid signature for a different digest", "Only an expired image tag", "Only a slow build cache"], "Identity and content binding both matter."),
    ("What does a configured registry replication rule fail to prove?", ["A particular release digest is pullable in the recovery region", "The source has a rule", "The destination registry exists"], "Per-release recovery needs a destination pull test."),
    ("Why can a running Pod mislead a rollback check?", ["Its node may have cached an image deleted from the registry", "It always re-pulls every layer on each request", "It rewrites the registry digest"], "A replacement Pod is a stronger pull test."),
    ("What should protect an untagged image from cleanup?", ["A live, pending, rollback, or recovery manifest still references its digest", "Its tag was once descriptive", "It has the smallest layer count"], "Retention must follow required digest references."),
    ("What can happen when public and private package indexes both serve one internal name?", ["An unintended public candidate can be selected", "The private index always wins", "The installer refuses every version"], "Package source rules must be explicit."),
    ("What completes the artifact trust drill?", ["Reviewed source, approved digest, verified signer, clean secret scan, and pull-tested rollback", "Only a green pull-request badge", "Only one configured registry rule"], "Each boundary requires its own observed result."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on CI trust, identity claims, build secrets, digest promotion, and rollback pulls.",
            sort_order=19700, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in project_related],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = "<p>Choose the result that proves a release crossed each trust boundary safely. A configured control or a familiar file name is not evidence of the exact deployed bytes.</p><h2>Review these lessons</h2>" + links(project_related) + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-cluster-control-failures", "quizzes/devops-cloud-boundary-decisions"]) + "<h3>Common Mistakes</h3><ul><li>Do not execute an untrusted artifact in a deployment job.</li><li>Do not equate a registry tag with a verified digest.</li></ul>"
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Artifact trust check</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": path, "title": titles[path]} for path in [project_path, quiz_path])

for source, targets in {
    "devops/github-actions-security": ["devops/untrusted-ci-artifact-handoff", "devops/ci-oidc-claim-boundary"],
    "devops/container-image-builds": ["devops/container-build-secret-boundary"],
    "devops/artifact-promotion": ["devops/registry-tag-mutation-race", "devops/rollback-image-retention"],
    "devops/supply-chain-verification": ["devops/signature-trust-rollover"],
    "devops/multi-region-failover": ["devops/registry-replica-promotion"],
    "devops/ci-cache-boundaries": ["devops/private-package-name-boundary"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Advanced follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1, "total_records": len(rows)}))
