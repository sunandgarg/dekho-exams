"""Replace DevOps preview stubs with an original, linked operations curriculum."""

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


def lesson(slug, title, summary, definition, practice, language, sample, cost, mistakes, related):
    specs.append(dict(path="devops/" + slug, title=title, summary=summary,
                      definition=definition, practice=practice, language=language,
                      sample=sample, cost=cost, mistakes=mistakes, related=related))


lesson("getting-started", "DevOps: map a change from commit to recovery",
       "Trace one production change through build, release, observation, and recovery.",
       "DevOps is a way of designing software delivery and operations as one feedback system. A change is not complete when a build succeeds; it is complete when its intended behavior is running, visible to operators, and recoverable. The useful unit of analysis is a specific change moving through a specific service, not a list of tools bought by the organization.",
       "For a ledger API, draw the path from a merged commit to a tested artifact, a production deployment, and the first signal that the new version works. Record who can stop the release and how they restore service if the new code fails. Measure change lead time and deployment frequency alongside change failure and recovery; a fast pipeline that produces repeated incidents is a poor pipeline. DORA now also tracks deployment rework, so treat metric definitions as versioned operational contracts. Start with one service and its actual event timestamps. The shell sketch below turns a release record into an explicit set of checks; connect each check to the real systems used by the team. A process diagram without a restore step is unfinished.",
       "bash", "release_id=ledger-2026-10-01-47\ncheck_artifact_digest \"$release_id\"\ncheck_test_result \"$release_id\"\ncheck_deployment_health \"$release_id\"\nrecord_recovery_owner \"$release_id\"",
       "Every gate adds wait time, but gates that detect a costly failure before production can reduce total recovery work. Capture the time spent queued, testing, and waiting for approval separately; otherwise a single lead-time number hides the bottleneck. The commands are a workflow sketch, not stock shell utilities. In a real pipeline, make a failed check stop promotion, persist the evidence, and avoid granting the check process deployment credentials it does not need.",
       ["Do not equate a green build with a healthy release.", "Do not optimize deployment frequency while ignoring failed deployments.", "Do not rely on an undocumented person as the recovery plan."],
       ["devops/core-concepts", "devops/continuous-integration", "devops/service-level-objectives"])

lesson("core-concepts", "DevOps feedback loops, ownership, and release boundaries",
       "Define the handoffs and evidence that make a service releasable.",
       "A delivery loop connects source control, repeatable verification, a versioned artifact, deployment, telemetry, and a recovery decision. Continuous integration checks whether a proposed change can be combined safely. Continuous delivery keeps a releasable artifact ready; continuous deployment sends a passing change to production without a separate manual release decision. Those are distinct choices, and neither removes operational ownership.",
       "An identity service can merge frequently while requiring a reviewed production promotion. The same artifact digest tested in staging should be the one promoted; rebuilding it between environments creates a new object with different dependency resolution and weakens the evidence. Name the owner of the pipeline, the service, and the incident response. Give each stage an input, output, and failure action. A release manifest makes that contract reviewable and can connect the deployment to a commit without relying on a mutable image tag. The fields below are a minimal record, not a complete deployment API. Keep environment settings separate from the artifact so the code identity does not change as it moves through environments.",
       "yaml", "service: identity-api\ncommit: 6b21d37\nartifactDigest: sha256:9a09c4f113a2\nenvironment: staging\nresult: verified\nrollbackOwner: identity-oncall",
       "Provenance records and telemetry consume storage, but losing them makes a failed release harder to diagnose. Set retention according to incident review needs and access policy. A short feedback loop is useful only when the checks are meaningful; a fast test suite that ignores database changes shifts the cost to production. Keep the release decision separate from build success and describe what happens when a check times out or returns no data.",
       ["Do not call a rebuilt image the same tested artifact.", "Do not treat continuous delivery as automatic production deployment.", "Do not leave ownership implicit at an environment handoff."],
       ["devops/git-change-control", "devops/artifact-promotion", "devops/incident-response"])

lesson("git-change-control", "Git change control: small merges and protected branches",
       "Use source history as the reviewed record for a deployable change.",
       "A protected main branch is a coordination boundary: changes enter through reviewed commits that satisfy checks, while production deployment refers to a specific commit or artifact. Short-lived branches reduce the time two developers spend editing divergent versions. A branch name is not a release identity because its target can move.",
       "For a claims service, split a schema migration and its reader change into compatible steps that can merge independently. Require the integration checks on the final merge result, not merely an old branch head. Review the changed behavior, migration path, and recovery plan. Prefer a small pull request that exposes one decision over a large batch that is difficult to revert. When a protected branch needs an emergency change, use an auditable exception with an owner and follow-up review. The command below verifies the commit recorded in a release file against the local repository before building; the actual protection policy is configured in the hosting service. Preserve commit identity when promoting an artifact, even if the release label is more readable to operators.",
       "bash", "expected_commit=$(cat release/claims-commit.txt)\nactual_commit=$(git rev-parse HEAD)\ntest \"$actual_commit\" = \"$expected_commit\"\ngit status --porcelain",
       "Frequent small merges create more CI runs but generally make failures easier to isolate. Cost also comes from review queue time; measure it before adding a blanket approval layer. The status command prints uncommitted changes but does not fail when output exists, so a real build script must reject a dirty tree explicitly. A protected branch cannot guarantee the runtime is healthy; it controls entry to source history, not deployed behavior.",
       ["Do not deploy a moving branch name as the release identity.", "Do not assume a successful check on an old branch head covers the merge result.", "Do not bypass branch rules without a recorded incident or exception."],
       ["devops/continuous-integration", "devops/database-change-safety", "devops/artifact-promotion"])

lesson("continuous-integration", "Continuous integration: test the merge candidate",
       "Run fast, deterministic checks before packaging a release.",
       "Continuous integration is the practice of combining changes frequently and verifying the combined result. A CI pipeline should fail on a broken build, test failure, or violated policy, then report which check failed. It is not a production health monitor and cannot validate behavior that only appears after traffic reaches the service.",
       "A dispatch API pipeline first checks formatting and types, then unit tests, then an integration test against a temporary database. Parallelize independent checks, but do not promote an image before every required result is known. Pin tool versions and dependency resolution so rerunning the same commit has interpretable results. The shell block shows the order within one job; a real runner needs isolated services, timeouts, cache keys, and explicit permissions. A flaky test should be repaired or quarantined with an owner and expiry rather than retried until it passes. Save a test report and the exact source commit for later diagnosis. A merge gate is effective only if the protected branch actually requires the job.",
       "bash", "set -euo pipefail\npython -m ruff check src tests\npython -m mypy src\npython -m pytest -q tests/unit\npython -m pytest -q tests/integration",
       "A full integration suite on every edit may increase queue time and discourage small changes. Keep a fast mandatory layer and schedule longer checks where they still block release when relevant. Caches lower compute cost but can hide stale dependencies; key them by lockfile and toolchain. Do not interpret a green unit suite as proof that migrations, deployment configuration, or external contracts are correct. Test reports should identify skipped tests as well as passed ones.",
       ["Do not let a flaky test pass by unlimited retry.", "Do not package before required gates complete.", "Do not forget to require the CI job in branch protection."],
       ["devops/git-change-control", "devops/artifact-promotion", "devops/database-change-safety"])

lesson("artifact-promotion", "Immutable artifacts and release provenance",
       "Promote the exact bytes that passed verification.",
       "An artifact is an output of a build, such as a container image. A tag is a human-friendly pointer that can be moved; a digest identifies specific image content. Promotion means taking the tested digest to the next environment rather than rebuilding from the same source. Provenance connects that output to its source revision and trusted build process.",
       "The payments worker is built once, scanned, and deployed to staging. When checks pass, production receives the same digest. Record the commit, build run, digest, scan result, and approval in one release record. A signature or attestation only helps if a deployment policy verifies the signer and its allowed source; storing an unsigned statement next to an image does not enforce anything. The manifest sketch uses a shortened digest for readability; substitute a real full SHA-256 digest before deployment. Rollback should also name an earlier approved digest, not an ambiguous latest tag. Keep the release record available during incident response so operators can answer which code and dependencies are running.",
       "yaml", "service: payments-worker\nsourceCommit: b73e49a\nbuildRun: 4721\nimage: registry.internal/payments-worker@sha256:9a09c4f113a2\nverifiedIn: staging\npromotionTarget: production",
       "Retaining images and attestations costs registry space, so define a retention period that preserves rollback candidates. Rebuilding per environment can save some storage yet creates verification gaps and often wastes compute. A digest alone does not prove the builder was trustworthy; identity, permissions, dependency pinning, and verification policy matter. Treat the sample digest as illustrative. A working image reference needs the full digest from the registry and an accessible registry endpoint.",
       ["Do not deploy a mutable latest tag as the only release identity.", "Do not infer trust from a digest without verifying its build origin.", "Do not delete every earlier image needed for rollback."],
       ["devops/container-image-builds", "devops/github-actions-security", "devops/progressive-delivery"])

lesson("container-image-builds", "Container builds: small runtime, explicit privilege",
       "Separate build tools from runtime files and control the build context.",
       "A container image packages an application filesystem and execution defaults. A multi-stage Dockerfile can compile or install dependencies in one stage and copy only runtime files into the final stage. This reduces unnecessary contents; it does not automatically make the image safe. The build context, base image updates, user identity, and dependency resolution remain part of the release decision.",
       "For a Go reconciliation worker, compile a static binary in a builder stage and run it as a nonroot numeric user in a small runtime stage. Add a .dockerignore that excludes local credentials, test reports, and version-control metadata; otherwise those files can enter the build context even when they are never copied into the final stage. Pin base images by digest for repeatability, then refresh them on a scheduled security cadence. Scan the final image and test it under the same user and filesystem permissions used in production. The sample is a pattern for a Go module whose main package is under cmd/reconciler; adjust the module path and base digest for the actual repository. A container process is still subject to network, capability, and host controls outside the Dockerfile.",
       "dockerfile", "FROM golang:1.25-alpine AS build\nWORKDIR /src\nCOPY go.mod go.sum ./\nRUN go mod download\nCOPY . .\nRUN CGO_ENABLED=0 go build -trimpath -o /out/reconciler ./cmd/reconciler\nFROM alpine:3.22\nRUN addgroup -S app && adduser -S -G app app\nCOPY --from=build /out/reconciler /usr/local/bin/reconciler\nUSER app\nENTRYPOINT [\"/usr/local/bin/reconciler\"]",
       "A smaller image can reduce transfer time and vulnerability surface, but a second stage adds build configuration to maintain. Alpine can have compatibility implications for applications that need glibc; this static Go build avoids that specific dependency. Cached modules speed repeat builds, while stale base layers can retain fixed vulnerabilities. The shown tags are mutable and should be pinned to real digests in a production repository. Do not put secrets in build arguments or source files; use a secret mount for build-time access and keep secret material out of layers.",
       ["Do not mistake a small image for a secured runtime.", "Do not include credentials in the build context.", "Do not pin a base image forever without an update process."],
       ["devops/artifact-promotion", "devops/kubernetes-deployments", "devops/secrets-and-configuration"])

lesson("github-actions-security", "GitHub Actions: narrow tokens and cloud trust",
       "Give each workflow job only the authority it needs.",
       "A CI workflow runs code from a repository event in a runner with an identity and a token. Its permissions are part of the threat model: a test job that only reads source does not need permission to write packages or mint an identity token. OpenID Connect can exchange a short-lived GitHub-issued identity token for cloud credentials when the cloud trust policy accepts the job's claims.",
       "A billing service has one unprivileged test job and a separate deployment job protected by an environment. Set a minimal default permission and grant id-token: write only to the deployment job that needs to request an OIDC token. The cloud provider must also restrict the accepted repository, branch or environment, and audience; id-token: write by itself grants no cloud role. Avoid running untrusted pull-request code in a privileged context. Pin third-party actions to reviewed commit SHAs in a real workflow and review updates deliberately. The fragment below shows only job permission boundaries, not a complete workflow. Environment review and branch restrictions are configured in repository settings and may depend on the plan and repository visibility.",
       "yaml", "name: billing-ci\non: [push]\npermissions: {contents: read}\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: make test\n  deploy:\n    needs: test\n    environment: production\n    runs-on: ubuntu-latest\n    permissions: {contents: read, id-token: write}\n    steps:\n      - run: ./release/promote-verified-digest.sh",
       "Splitting jobs increases runner startup time but keeps deployment authority away from test code. A token limited in GitHub can still be dangerous if the cloud trust policy accepts too many claims. The fragment deliberately omits checkout and OIDC exchange steps; copying it alone will not deploy. Audit who can change workflow files, which branches may reach production, and whether environment protection actually runs. Never print credentials or identity tokens in job logs.",
       ["Do not use id-token: write as a substitute for a restrictive cloud trust policy.", "Do not run untrusted pull-request code with deployment credentials.", "Do not assume an environment name creates approval rules automatically."],
       ["devops/continuous-integration", "devops/artifact-promotion", "devops/secrets-and-configuration"])

lesson("terraform-state-and-plan", "Terraform state: shared ownership and safe plans",
       "Protect the mapping between declared resources and real infrastructure.",
       "Terraform state records which remote objects correspond to resources in configuration. A plan compares configuration and observed state before an apply. Teams need a protected remote state store with access control, versioning, and a backend that supports locking; a local state file committed to Git is neither a safe coordination method nor a suitable secret store.",
       "For a fraud-review service, keep network infrastructure and application-level resources in separately owned state units. Run validation and a plan on the proposed configuration, then apply the approved revision with the same provider lockfile and a serialized state writer. Treat saved plan files and state as sensitive because provider attributes can contain secret material. A plan is also time-sensitive: another actor may change infrastructure after it was reviewed. Recheck drift before apply and abort if the target state no longer matches expectations. The commands below demonstrate review and apply order but do not configure a backend; choose a backend with locking and protected access before collaborative use. Never disable locking to make a stuck pipeline pass.",
       "bash", "terraform init -input=false\nterraform fmt -check\nterraform validate\nterraform plan -out=reviewed.plan\nterraform apply reviewed.plan",
       "Remote state adds storage and access-management cost. Locking serializes writes and may make a queued apply wait, which is preferable to corrupting shared state. A saved plan can become stale if remote resources change; keep the approval window short and let the apply fail safely when assumptions no longer hold. Do not print state or plan output into broadly visible logs. Commit configuration and the provider lockfile, while excluding state, state backups, and saved plans from version control.",
       ["Do not commit state or saved plans.", "Do not disable locking to clear contention.", "Do not apply an old plan after unrelated infrastructure changes."],
       ["devops/gitops-reconciliation", "devops/secrets-and-configuration", "devops/backup-and-recovery"])

lesson("gitops-reconciliation", "GitOps reconciliation: desired state and drift",
       "Let a controller compare an approved repository revision with cluster state.",
       "GitOps uses a versioned desired state as the reviewed input to a reconciliation controller. The controller observes the live system and applies differences according to its configured policy. This is different from a CI job that directly mutates a cluster after building an image; the cluster-side controller can work without granting the CI runner broad cluster access.",
       "A case-review service updates an image digest in a deployment repository through a pull request. After review, the controller notices the new commit and synchronizes the cluster. Decide separately whether automatic sync, self-heal, and pruning are enabled. Self-heal can reverse a manual emergency edit, while pruning can delete a resource removed from the repository. During an incident, operators need a documented way to pause reconciliation or commit a safe rollback; a one-off kubectl edit may be overwritten. The small manifest shows the desired image identity, not a full controller setup. Record the repository revision and the observed cluster revision so drift has an owner and a timestamp.",
       "yaml", "apiVersion: apps/v1\nkind: Deployment\nmetadata: {name: case-review}\nspec:\n  replicas: 3\n  selector: {matchLabels: {app: case-review}}\n  template:\n    metadata: {labels: {app: case-review}}\n    spec:\n      containers:\n        - name: api\n          image: registry.internal/case-review@sha256:9a09c4f113a2",
       "Reconciliation uses API calls and controller resources, but its larger cost is operational: a mistaken desired state can be applied repeatedly. Review deletion and namespace scope before enabling pruning. The sample digest is shortened and must be replaced with a real full digest. The manifest also omits resource requests, health probes, and security settings for focus; use the linked deployment lessons before running it. A synchronized controller does not prove the application is serving correct responses.",
       ["Do not assume every manual hotfix survives self-heal.", "Do not enable pruning without a deletion review path.", "Do not equate synchronized configuration with healthy user traffic."],
       ["devops/terraform-state-and-plan", "devops/kubernetes-deployments", "devops/progressive-delivery"])

lesson("kubernetes-deployments", "Kubernetes Deployment: rolling update capacity",
       "Choose a rollout budget that the cluster and service can support.",
       "A Kubernetes Deployment manages ReplicaSets for a usually stateless workload and replaces Pods toward a desired template. A rolling update can create extra Pods through maxSurge while limiting unavailable Pods through maxUnavailable. Those settings constrain replacement capacity; they do not prove a request is successful or guarantee a database change is compatible.",
       "A document-index API runs four replicas and permits one extra Pod while keeping all four available during an update. Verify that the cluster has room for the temporary fifth Pod and that downstream services can tolerate overlap between old and new versions. Readiness must gate service traffic to each new Pod. The fragment focuses on rollout arithmetic; add the complete Pod template, probes, resources, and security context before deployment. If scheduling cannot place the surge Pod, the rollout may stall. If readiness always returns success, the controller can replace healthy old Pods with broken new ones. Record the image digest and use rollout status with an explicit timeout. A rollback to an earlier Pod template also has to be compatible with any schema migration already applied.",
       "yaml", "strategy:\n  type: RollingUpdate\n  rollingUpdate:\n    maxSurge: 1\n    maxUnavailable: 0\nreplicas: 4\nprogressDeadlineSeconds: 240",
       "With four desired replicas, the fragment allows up to five Pods during the rollout and aims to keep four available. That extra Pod consumes CPU, memory, connections, and possibly a license slot. maxUnavailable: 0 cannot prevent user-visible errors if readiness is wrong or the shared database fails. Percent values have rounding rules, so absolute counts are clearer for a small replica set. Track stalled rollout conditions and stop promotion when the progress deadline is exceeded.",
       ["Do not set maxSurge without checking spare capacity.", "Do not expect replica availability to prove application correctness.", "Do not roll back code that cannot read the migrated schema."],
       ["devops/kubernetes-probes", "devops/database-change-safety", "devops/progressive-delivery"])

lesson("kubernetes-probes", "Kubernetes probes: startup, readiness, and liveness",
       "Make probe responses reflect distinct operational questions.",
       "A startup probe gives a slow-starting container time to initialize before liveness and readiness take over. A readiness probe decides whether a Pod should receive service traffic. A liveness probe decides whether Kubernetes should restart a container. These roles should use different failure criteria when the application can be alive but temporarily unable to serve.",
       "A search API loads an index before accepting traffic. Its startup endpoint fails until initialization finishes; readiness checks whether it can serve the current request class; liveness checks for a stuck process that a restart could plausibly repair. Do not make liveness depend on a shared database outage, because that can restart every replica during the same downstream failure. The fragment shows probe configuration for a container exposing port 8080. The handlers and timing need load tests: a probe that times out only during normal peak CPU can turn a healthy service into a restart loop. Watch startup duration and restart counts after each release, and verify readiness goes false during a deliberate shutdown before the process exits.",
       "yaml", "startupProbe:\n  httpGet: {path: /health/startup, port: 8080}\n  periodSeconds: 3\n  failureThreshold: 40\nreadinessProbe:\n  httpGet: {path: /health/ready, port: 8080}\n  periodSeconds: 5\nlivenessProbe:\n  httpGet: {path: /health/live, port: 8080}\n  periodSeconds: 10",
       "The startup settings allow roughly two minutes for initialization before failure, aside from request timeouts and scheduling effects. Frequent probes create network and handler work; keep endpoints cheap and bounded. Readiness failure removes the Pod from normal service routing but does not restart it, while liveness failure can trigger a restart. A restart may make a transient dependency outage worse. Test thresholds under realistic CPU pressure and during termination, not only on a quiet laptop.",
       ["Do not use the same dependency-heavy check for liveness and readiness.", "Do not set startup thresholds below ordinary cold-start time.", "Do not assume readiness catches incorrect business responses."],
       ["devops/kubernetes-deployments", "devops/observability-signals", "devops/incident-response"])

lesson("secrets-and-configuration", "Secrets and configuration across the delivery path",
       "Keep credentials out of source, images, artifacts, and broad logs.",
       "Configuration changes runtime behavior without changing application code. A secret is configuration whose disclosure grants access or reveals protected data. Encoding a value as base64, including in a Kubernetes Secret manifest, is not encryption. The storage system, transport, runtime mount, role permissions, and rotation procedure all matter.",
       "A settlement worker reads a database credential from a restricted runtime secret source rather than baking it into the image. Give the workload only the secret it needs, protect the cluster store with encryption at rest and access control, and avoid printing environment variables during troubleshooting. Rotate a credential by introducing the new value, verifying connections, then revoking the old one; abrupt replacement can strand long-lived connections. Use separate identities for CI, deployment, and application runtime. The YAML fragment shows a key reference, not the secret value or its creation. Whether an update reaches a running process depends on the injection method and application behavior. Test revocation and incident response, not just initial access.",
       "yaml", "env:\n  - name: SETTLEMENT_DB_PASSWORD\n    valueFrom:\n      secretKeyRef:\n        name: settlement-db\n        key: password",
       "A managed secret service and frequent rotation add requests and operational work, but reduce the blast radius of a leaked credential. Environment variables are convenient yet can be exposed through process inspection or accidental diagnostics; a mounted file or direct secret client may fit stricter environments. No storage mechanism prevents an authorized process from mishandling the secret. Restrict log access and set retention. Check that backups and disaster-recovery copies protect the same material.",
       ["Do not commit base64-encoded credentials.", "Do not share one cloud identity between CI and the running service.", "Do not rotate a credential without testing live connection behavior."],
       ["devops/github-actions-security", "devops/terraform-state-and-plan", "devops/backup-and-recovery"])

lesson("progressive-delivery", "Progressive delivery: canary checks and rollback",
       "Expose a new version to a measured share of traffic before full promotion.",
       "Progressive delivery changes exposure in stages while observing a defined health signal. A canary is useful when the new version can run alongside the old one and the platform can route or select a subset of traffic. A rollback returns code or routing to a prior version; it does not undo an irreversible database write or restore deleted data.",
       "A notifications API sends a small slice of requests to a new digest, then compares error rate and latency with the old version. Set the decision window before deployment, include enough requests to make the signal meaningful, and halt when the threshold is crossed. Avoid a canary that receives only low-risk traffic while the production change mostly affects high-risk paths. Track the new digest in each log and metric label without using unbounded request IDs as metric labels. The YAML sketch is a release policy document, not a controller-specific API. Automate pause and rollback only when the signal and control path have been tested; otherwise keep an operator ready with a known safe digest and a short command sequence. Follow the canary with a full-rollout watch because new failures may appear only at scale.",
       "yaml", "service: notifications-api\nnewVersionTrafficPercent: 7\nobservationMinutes: 23\nabortWhen:\n  errorRatePercentAbove: 1.8\n  p95LatencyMsAbove: 420\nrollbackDigest: sha256:9a09c4f113a2",
       "A canary consumes extra capacity because old and new versions overlap. Low traffic can make a short window statistically weak; set a minimum event count and use representative requests. Metrics arrive with delay, so a controller should not promote solely because no samples have appeared. The sample values are illustrative and require calibration against this service's baseline and SLO. Rollback may restore request handling quickly, yet a schema or queue-format change can make older code incompatible.",
       ["Do not treat missing telemetry as a healthy canary.", "Do not assume code rollback reverses data changes.", "Do not route only easy traffic to the canary and call it representative."],
       ["devops/artifact-promotion", "devops/service-level-objectives", "devops/database-change-safety"])

lesson("database-change-safety", "Database change safety: expand, migrate, contract",
       "Make schema changes compatible with both old and new application versions.",
       "An expand-and-contract migration introduces a new representation while old code still runs, copies or dual-writes data as needed, changes readers after verification, then removes the old representation later. The phases matter because a rolling deployment and rollback can leave two application versions alive at once. A schema change that renames a column in place can break the old version immediately.",
       "A parcel service replaces a free-text delivery state with a constrained state code. First add the new nullable column and teach new writers to populate it while retaining the old field. Backfill in bounded batches with checkpoints, then compare counts and sample records. Change readers only after the data is complete, and defer dropping the old column until the rollback window closes. The SQL fragment shows only the expansion step; the application dual-write, backfill job, and contract migration are separate reviewed changes. On a large table, even adding a column can have database-specific lock or rewrite effects. Rehearse against production-like volume, watch replication lag, and plan what happens if the backfill stops halfway.",
       "sql", "ALTER TABLE parcel_events\n  ADD COLUMN delivery_state_code VARCHAR(32);\nCREATE INDEX parcel_events_state_code_idx\n  ON parcel_events (delivery_state_code);",
       "Backfills consume I/O and can contend with user queries. An index build may block writes depending on the database and command; use the database's online/concurrent mechanism where applicable. Dual-writing adds application complexity and can create divergent values, so measure mismatches until the old path is retired. Rolling back code is safe only while the old field remains valid and populated. Do not assume a migration is reversible merely because its SQL file has a down section.",
       ["Do not drop an old column in the same release that introduces its replacement.", "Do not run an unbounded backfill at peak traffic.", "Do not claim rollback works without testing mixed application versions."],
       ["devops/kubernetes-deployments", "devops/progressive-delivery", "devops/backup-and-recovery"])

lesson("observability-signals", "Observability: join metrics, logs, and traces",
       "Collect signals that explain user impact and locate the failing boundary.",
       "Metrics aggregate measurements over time, logs record discrete events, and traces connect work across components. None substitutes for the others. A useful dashboard starts with a user-facing operation and its latency, error, and traffic signals, then lets an operator follow a failing request toward the responsible service or dependency.",
       "A receipt API records a request duration histogram and a result counter, emits structured logs with a trace identifier, and propagates trace context to the document service. Name operations by stable route templates rather than raw customer IDs. Keep sensitive payloads out of telemetry. During a partial failure, compare the affected route and deployment version, then inspect a sampled trace for the slow span. The PromQL sketch calculates five-minute error ratio using only requests classified as server failures; adapt the metric names and status labels to the actual instrumentation. Also watch client-visible failures outside HTTP 5xx, such as invalid responses or queue delays. A dashboard that shows a green CPU graph while customers cannot receive receipts has the wrong primary signal.",
       "promql", "sum(rate(receipt_requests_total{result=\"server_error\"}[5m]))\n/\nsum(rate(receipt_requests_total[5m]))",
       "High-cardinality labels such as request IDs or email addresses can make metric storage costly and slow. Put per-request identifiers in logs and traces instead, with retention and access rules. Sampling lowers trace cost but can miss rare failures; tune it with the incident needs of the service. A zero denominator produces an absent or invalid ratio, which is not proof of health. Pair alert rules with minimum traffic and an explicit no-data decision.",
       ["Do not put personal identifiers in metric labels.", "Do not treat no data as zero errors.", "Do not instrument infrastructure while omitting user-visible operations."],
       ["devops/kubernetes-probes", "devops/service-level-objectives", "devops/incident-response"])

lesson("service-level-objectives", "SLOs and error budgets: turn reliability into a decision",
       "Define a measurable user promise and its allowed failure budget.",
       "A service-level indicator is a measured ratio or latency distribution for a user-relevant operation. A service-level objective sets a target for that indicator over a defined window. The error budget is the allowed miss implied by the target, not a pool of incidents the team is obliged to spend. Alerting should focus on sustained budget burn and actionable user impact.",
       "For a document-download endpoint, suppose 240,000 eligible requests occur in a 28-day window and the objective is 99.92 percent successful responses. The allowed failures are 192, since 240,000 times 0.0008 equals 192. If 151 eligible requests have failed, 41 failures remain under this simplified request-count model. Exclude only events specified in the SLI definition; silently dropping inconvenient failures destroys the measure. Publish the numerator, denominator, window, exclusions, and no-traffic handling together. Review a fast-burn alert for an acute outage and a slower alert for a persistent regression. Pause risky releases when the agreed policy says the budget is depleted, while keeping room for emergency fixes. The small configuration sketch records the contract, not an alerting-system API.",
       "yaml", "service: document-download\nwindowDays: 28\neligibleRequests: 240000\ntargetSuccessPercent: 99.92\nallowedFailures: 192\nobservedFailures: 151\nremainingFailures: 41",
       "A request-count SLO can hide a small group of users who fail repeatedly, so segment and inspect the distribution without inflating metric cardinality. Longer windows smooth noise but react slowly; shorter windows catch regressions yet can swing with low traffic. Keep the arithmetic and event filters reproducible. Alerting on every failed request creates noise, while waiting until all 192 failures are spent may react too late. A budget policy should state who can decide exceptions and when it is reviewed.",
       ["Do not change the eligible-request definition after a bad week.", "Do not equate missing traffic with perfect availability.", "Do not page on a threshold without an action an operator can take."],
       ["devops/observability-signals", "devops/progressive-delivery", "devops/incident-response"])

lesson("incident-response", "Incident response: contain impact, then learn",
       "Run incidents with named roles, timestamps, and a reversible first action.",
       "An incident is an unplanned service disruption or serious risk that needs coordinated response. The first objective is to reduce user impact; diagnosis and long-term repair can follow once the service is stable. A runbook connects symptoms to safe checks, escalation contacts, and the quickest validated mitigation.",
       "If a deployment raises checkout failures, assign an incident lead and an operator, record the start and affected paths, then pause rollout or route back to the last known good digest. Keep a single incident timeline. A communications owner can provide a short status to stakeholders without interrupting the person executing the mitigation. The shell sketch reads a rollout and initiates a rollback, but run it only after confirming the prior revision is compatible with current data. If the problem came from a migration or external dependency, reversing a Deployment may not help. After recovery, write a review that distinguishes the trigger, conditions that amplified it, detection delay, and actions with owners and dates. Avoid reducing the review to who clicked a button.",
       "bash", "kubectl -n checkout rollout status deployment/checkout-api --timeout=90s\nkubectl -n checkout rollout history deployment/checkout-api\nkubectl -n checkout rollout undo deployment/checkout-api\nkubectl -n checkout rollout status deployment/checkout-api --timeout=180s",
       "Fast rollback can shorten impact but may create another failure if schema or event formats are incompatible. Keep rollback drills current and record which revisions remain safe. An incident bridge and logs cost attention; explicit roles prevent several people from issuing conflicting changes. Preserve evidence before cleanup where possible, but do not delay a known safe mitigation merely to capture perfect diagnostics. Use the incident review to change a concrete control, test, or signal, then verify that change later.",
       ["Do not run rollout undo without checking data compatibility.", "Do not let several operators change the same service without coordination.", "Do not close an incident review with actions that have no owner."],
       ["devops/service-level-objectives", "devops/backup-and-recovery", "devops/getting-started"])

lesson("backup-and-recovery", "Backups and disaster recovery: prove the restore path",
       "Set recovery objectives and verify that protected copies can be used.",
       "A backup is a recoverable copy of data or configuration. Recovery point objective describes the maximum acceptable data loss measured in time; recovery time objective describes the target time to restore useful service. A scheduled backup alone proves neither objective. Restore testing must include keys, dependencies, application compatibility, and a way to validate the recovered data.",
       "A dispute service targets a recovery point within 17 minutes and useful read access within 74 minutes. That implies backup or replication frequency, retention, and restore capacity appropriate to those numbers. Encrypt copies, restrict deletion privileges, and keep a copy isolated from the credentials that can destroy the primary. In a drill, restore into a separate environment, run data-integrity checks, and measure time from declared failure to a verified user operation. The checklist below is a runbook outline, not executable commands. Include the database schema version and image digest expected by each restore point; an old backup with only new code can be unusable. Test a partial restore and a lost encryption key scenario, not only the happy path.",
       "text", "Recovery drill: dispute-service\nRPO target: 17 minutes\nRTO target: 74 minutes\n1. Select an isolated backup point and verify its checksum.\n2. Restore data, keys, schema version, and application digest.\n3. Run integrity queries and one user-facing read.\n4. Record observed data gap and elapsed recovery time.",
       "Frequent backups and geographically separate copies cost storage and network transfer. A cheaper policy may miss the agreed recovery point, while a fast snapshot is useless if a restore takes too long. Measure both objectives in drills and report misses. Replication can copy corruption or deletion quickly; keep independent point-in-time copies. Rotation and key escrow are operational parts of recovery, because inaccessible encryption keys make intact backup files unusable.",
       ["Do not call a completed backup job a successful restore test.", "Do not give the production deletion identity access to every backup copy.", "Do not forget application and schema compatibility at the restore point."],
       ["devops/database-change-safety", "devops/incident-response", "devops/secrets-and-configuration"])


titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
titles[project_hub] = "DevOps projects"
titles["devops/practice-project"] = "Project: release and recover a ledger API"
titles[quiz_hub] = "DevOps checks"
titles["quizzes/devops-delivery"] = "DevOps delivery decisions"
titles["quizzes/devops-operations"] = "DevOps operations decisions"


def links(paths):
    return "<ul>" + "".join(f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>' for path in paths) + "</ul>"


for item in specs:
    assert all(target in titles for target in item["related"]), item["path"]


groups = [
    ("Delivery foundations", "Follow a change through review, verification, and promotion.", ["getting-started", "core-concepts", "git-change-control", "continuous-integration", "artifact-promotion"]),
    ("Build and secure", "Package one verified artifact and narrow job authority.", ["container-image-builds", "github-actions-security", "secrets-and-configuration"]),
    ("Infrastructure and release", "Control desired state, rollout capacity, compatibility, and rollback.", ["terraform-state-and-plan", "gitops-reconciliation", "kubernetes-deployments", "kubernetes-probes", "progressive-delivery", "database-change-safety"]),
    ("Operate and recover", "Measure user impact, respond to incidents, and prove restoration.", ["observability-signals", "service-level-objectives", "incident-response", "backup-and-recovery"]),
]
hub = by_path[course]
hub.update(title="DevOps: delivery, infrastructure, and reliable operations",
           summary="An ordered path from reviewed commits to verifiable releases and tested recovery.", updated_at=stamp)
hub["data"] = {
    "subject_root": course, "section_path": course,
    "content_format": "html", "seo_ready": True,
    "modules": [{"title": title, "summary": summary, "lessons": ["devops/" + slug for slug in slugs]} for title, summary, slugs in groups],
    "resource_tabs": [{"title": "Tutorial", "path": course}, {"title": "Projects", "path": project_hub}, {"title": "Checks", "path": quiz_hub}],
}
hub["body"] = (
    "<p>DevOps connects the code change, the deployed artifact, the observed user result, and the recovery path. Work through one service and retain the commit, digest, deployment, and incident evidence that ties those stages together.</p>"
    + "".join(f"<h2>{html.escape(title)}</h2><p>{html.escape(summary)}</p>" + links(["devops/" + slug for slug in slugs]) for title, summary, slugs in groups)
    + "<h2>Apply and check</h2>" + links([project_hub, quiz_hub])
)


for order, item in enumerate(specs):
    path = item["path"]
    row = by_path.get(path) or copy.deepcopy(by_path["devops/getting-started"])
    section = course
    row.update(path=path,
               title=item["title"], summary=item["summary"], category="DevOps",
               subject="devops", difficulty="Intermediate" if order > 4 else "Beginner",
               tags=["devops", "operations"], sort_order=17000 + order,
               status="published", published_at=stamp, updated_at=stamp)
    row["data"] = {"kind": "tutorial", "reading_minutes": 6,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": section, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in item["related"]]}
    row["body"] = (
        f"<p>{html.escape(item['definition'])}</p><h2>Operational decision</h2>"
        f"<p>{html.escape(item['practice'])}</p>"
        f'<pre><code class="language-{item["language"]}">{html.escape(item["sample"])}</code></pre>'
        f"<h2>Cost and verification</h2><p>{html.escape(item['cost'])}</p>"
        + "<h3>Common Mistakes</h3><ul>"
        + "".join(f"<li>{html.escape(mistake)}</li>" for mistake in item["mistakes"])
        + "</ul><h2>Connected lessons</h2>" + links([course, *item["related"]])
    )
    if path not in by_path:
        row["id"] = str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path))
        row["created_at"] = stamp
        rows.append(row)


project = by_path["devops/practice-project"]
project.update(title="Project: release and recover a ledger API", summary="Build a reviewable release record, canary gate, rollback, and restore drill.",
               difficulty="Intermediate", updated_at=stamp, tags=["devops", "project"])
project["data"] = {"kind": "project", "reading_minutes": 9, "author_path": "authors/aitrove-editorial",
                   "subject_root": course, "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in ["devops/continuous-integration", "devops/artifact-promotion", "devops/progressive-delivery", "devops/incident-response"]]}
project["body"] = (
    "<p>This project assembles a release path for a ledger API that records invoice adjustments. The deliverable is a reviewable release packet, not a screenshot of a green pipeline. Use a disposable environment and sample records; the exercise should never require production credentials.</p>"
    "<h2>Build the packet</h2><p>Choose one commit. Run formatting, unit tests, and an integration test against an isolated database. Build an image once, record its full digest, and promote that digest to a staging namespace. Store the commit, test run, image digest, schema revision, and operator name in a release record. Configure readiness separately from liveness and prove that a deliberately unhealthy new Pod receives no normal traffic. Verify the deployment controller reaches its expected available replica count before exposing more users.</p>"
    "<pre><code class=\"language-yaml\">service: ledger-api\ncommit: 6b21d37\nartifact: registry.internal/ledger-api@sha256:9a09c4f113a2\nschemaRevision: ledger_047\nstagingCheck: pending\ncanaryCheck: pending\nrollbackDigest: sha256:4b66e1a2217c\nrestoreDrill: pending</code></pre>"
    "<h2>Break it on purpose</h2><p>Inject a predictable server error into one endpoint and send a small, representative traffic slice to the candidate. Set an error-rate stop rule and require enough requests to make the comparison useful. When the rule fires, pause promotion and route traffic to the earlier verified digest. Record how long detection and recovery took. Then restore a sample backup into a fresh environment and verify both a row count and one user-facing read. The packet is complete only when another engineer can repeat the release, rollback, and restore from the recorded steps.</p>"
    "<h2>Cost and verification</h2><p>The canary needs extra capacity, and an isolated restore needs storage and time. Budget both before starting. The shortened digests above are illustrative and must be replaced by full registry digests in a real packet. A code rollback does not undo schema or data changes, so keep the previous reader compatible until the exercise's rollback window ends. Review the packet for leaked credentials and remove temporary resources after preserving the evidence.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not rebuild the image between staging and production.</li><li>Do not count missing canary samples as success.</li><li>Do not skip the restore drill after a successful backup job.</li></ul>"
    "<h2>Reference lessons</h2>" + links(["devops/continuous-integration", "devops/artifact-promotion", "devops/kubernetes-probes", "devops/progressive-delivery", "devops/backup-and-recovery", course])
)
project_hub_row = by_path[project_hub]
project_hub_row.update(title="DevOps projects", summary="Apply delivery and recovery decisions in a disposable service environment.",
                       category="DevOps", updated_at=stamp)
project_hub_row["data"] = {"subject_root": course, "section_path": project_hub,
                           "content_format": "html", "seo_ready": True,
                           "modules": [{"title": "Release and recovery", "summary": "Produce evidence from build through restore.", "lessons": ["devops/practice-project"]}]}
project_hub_row["body"] = "<p>Work through a complete release and recovery exercise with a disposable ledger service. Preserve evidence of the artifact, traffic check, rollback, and restored data.</p><h2>Project</h2>" + links(["devops/practice-project"]) + "<h2>Prepare first</h2>" + links(["devops/artifact-promotion", "devops/service-level-objectives", course])


quiz_sets = [
    ("quizzes/devops-delivery", "DevOps delivery decisions", [
        ("What should production receive after staging tests pass?", ["The same verified digest", "A rebuilt image with the same tag", "The current main branch name"], 0, "Promotion preserves the tested bytes."),
        ("What does a protected branch control?", ["Entry to source history", "Runtime health", "Database replication lag"], 0, "Branch rules gate merges, not user requests."),
        ("What should a flaky CI test trigger?", ["A repair or owned quarantine", "Unlimited retries", "Removal of the merge gate"], 0, "Retries can hide instability."),
        ("Why use a full image digest?", ["It identifies exact image content", "It grants cloud access", "It measures request latency"], 0, "Tags can move."),
        ("What belongs in a build context exclusion?", ["Local credentials", "Required source files", "The application entry point"], 0, "Private local files should not reach the builder."),
        ("What does id-token: write provide?", ["Permission to request an identity token", "Automatic cloud administrator access", "Approval to merge"], 0, "The cloud trust policy still controls role exchange."),
        ("What protects shared Terraform state from concurrent writers?", ["Backend locking", "A local file committed to Git", "A saved screenshot"], 0, "A supported backend serializes writes."),
        ("What may GitOps self-heal do to a manual cluster edit?", ["Revert it to repository state", "Guarantee a healthy response", "Encrypt every secret"], 0, "The controller reconciles toward declared state."),
        ("What does maxSurge: 1 permit with four desired Pods?", ["A temporary fifth Pod", "A permanent fifth replica", "One fewer available Pod"], 0, "Surge allows extra capacity during rollout."),
        ("What does readiness failure do?", ["Remove a Pod from normal service routing", "Always restart the container", "Delete the database"], 0, "Liveness is the restart signal."),
        ("What is the safe first phase of a column replacement?", ["Add a compatible new column", "Drop the old column", "Rename the old column in place"], 0, "Old and new application versions must overlap."),
        ("What is the release identity for rollback?", ["An earlier approved digest", "The latest tag", "A branch that may move"], 0, "Rollback needs an exact known-good artifact."),
    ], ["devops/continuous-integration", "devops/artifact-promotion", "devops/terraform-state-and-plan", "devops/kubernetes-deployments"]),
    ("quizzes/devops-operations", "DevOps operations decisions", [
        ("What makes a canary result meaningful?", ["Representative traffic and enough samples", "No telemetry", "Only internal requests"], 0, "A weak sample can miss failures."),
        ("What can code rollback leave unchanged?", ["Irreversible data writes", "The image digest", "The previous Pod template"], 0, "Data recovery is separate."),
        ("Which liveness check is risky during a database outage?", ["One that requires the database", "A cheap process check", "A check with a timeout"], 0, "It may restart every replica."),
        ("Is a base64 Kubernetes Secret encrypted by base64?", ["No", "Yes", "Only after a restart"], 0, "Encoding does not protect a value."),
        ("Where should request IDs go?", ["Logs and traces", "Unbounded metric labels", "Image tags"], 0, "High-cardinality labels are costly."),
        ("What does a no-data error-rate graph prove?", ["Nothing about service health", "Perfect success", "A completed restore"], 0, "Missing samples need an explicit decision."),
        ("At 240000 requests and 99.92 percent success, how many failures are allowed?", ["192", "41", "240"], 0, "Multiply 240000 by 0.0008."),
        ("What should an incident lead prioritize first?", ["Reducing user impact", "Assigning blame", "Polishing the timeline"], 0, "Containment precedes deeper review."),
        ("Before rollout undo, what must be checked?", ["Old code compatibility with current data", "The newest tag name", "The number of comments"], 0, "A schema change can make older code unsafe."),
        ("What proves a backup can meet recovery needs?", ["A measured restore drill", "A scheduled backup job", "A green storage dashboard"], 0, "Restoration must be tested."),
        ("What does RPO describe?", ["Maximum acceptable data loss in time", "Time to review a pull request", "Maximum CPU use"], 0, "RPO bounds the recovery point."),
        ("What should a post-incident action include?", ["An owner and a verification path", "Only a broad aspiration", "A blame statement"], 0, "Concrete actions must be checked later."),
    ], ["devops/progressive-delivery", "devops/observability-signals", "devops/service-level-objectives", "devops/backup-and-recovery"]),
]
quiz_subject = copy.deepcopy(by_path["css/quizzes"])
quiz_subject.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_hub)), path=quiz_hub,
                    title=titles[quiz_hub], summary="Check release, infrastructure, and recovery decisions.",
                    category="DevOps", subject="devops-quizzes", tags=["devops", "quiz"],
                    sort_order=17200, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz_subject["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html", "seo_ready": True,
                        "modules": [{"title": "Decision checks", "summary": "Use the linked lessons to explain each answer.", "lessons": [item[0] for item in quiz_sets]}]}
quiz_subject["body"] = "<p>These checks ask what a release or incident decision actually changes. Review the linked lesson when an answer is uncertain.</p><h2>Checks</h2>" + links([item[0] for item in quiz_sets]) + "<h2>Curriculum</h2>" + links([course, project_hub])
rows.append(quiz_subject)
for order, (path, title, questions, related) in enumerate(quiz_sets):
    quiz = copy.deepcopy(by_path["quizzes/css-native-states-navigation"])
    quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                title=title, summary="Twelve operational decisions with explanations and linked lessons.",
                category="DevOps", subject="devops-quizzes", tags=["devops", "quiz"],
                sort_order=17210 + order, published_at=stamp, created_at=stamp, updated_at=stamp)
    quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                    "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                    "related": [{"path": target, "title": titles[target]} for target in related],
                    "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                       answer=(answer - index % 3) % 3, explanation=explanation)
                                  for index, (prompt, options, answer, explanation) in enumerate(questions)]}
    quiz["body"] = "<p>Choose the action that preserves the evidence or reduces risk in the stated situation. Each answer has a short explanation.</p><h2>Review these lessons</h2>" + links(related) + "<h2>More DevOps checks</h2>" + links([quiz_hub, quiz_sets[1 - order][0]]) + "<h3>Common Mistakes</h3><ul><li>Do not treat a passing check as proof of production health.</li><li>Do not choose a rollback without checking data compatibility.</li></ul>"
    rows.append(quiz)

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"devops_lessons": len(specs), "projects": 1, "quiz_banks": len(quiz_sets), "total_records": len(rows)}))
