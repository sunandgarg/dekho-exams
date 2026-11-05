"""Add Terraform ownership and state failure contracts to the local DevOps preview."""

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
    "terraform-provider-lock-integrity", "Terraform provider locks: review the executable dependency",
    "Pin provider packages and distinguish them from remote module selections.",
    "A Terraform root configuration resolves providers and modules through different mechanisms. Its dependency lock file records selected provider versions and package checksums. It does not lock remote module versions. A broad module constraint can therefore select a newer module on a later initialization even while the provider lock file remains unchanged. A reviewed infrastructure change must identify both inputs: the provider package that will execute API calls and the module code that will declare resources.",
    "For a receipt platform, commit the root dependency lock file with the configuration. When upgrading a provider, review the lock-file diff beside the plan and run initialization on the supported runner platforms before promotion. Pin the remote network module to an exact approved version; review a module version change as a code change, because it can add or remove resources without modifying the provider entry. The fragment shows the two separate controls. Verify the installed provider source, selected version, and checksums from the actual runner, and inspect whether a private mirror or cache changes the trust path. A checksum match proves the selected package matches the recorded bytes; it does not prove the package is safe. Keep the change traceable to a tested plan and isolate the upgrade from unrelated address moves.",
    "hcl", 'terraform {\n  required_providers {\n    aws = {\n      source  = "hashicorp/aws"\n      version = "~> 6.0"\n    }\n  }\n}\n\nmodule "receipt_network" {\n  source  = "app.terraform.io/ledger-team/network/aws"\n  version = "3.4.2"\n}',
    "Pinned selections reduce surprise but create maintenance work: security fixes and API compatibility updates arrive only after a reviewed upgrade. Cross-platform checksums add a small amount of lock-file data; module version pins need explicit release tracking. Provider initialization downloads and verifies packages, while a plan can still be expensive because it refreshes remote resources. Measure changed resource count and unexpected replacements after each dependency upgrade, then compare it with a plan made from the previous dependency set.",
    ["Do not assume the dependency lock file freezes remote module versions.", "Do not hand-edit checksums to make an unverified package install.", "Do not combine provider upgrades and state address moves without a separate review boundary."],
    ["devops/terraform-module-contracts", "devops/terraform-state-and-plan", "devops/supply-chain-verification", "devops/terraform-address-refactoring"],
)

lesson(
    "terraform-import-ownership", "Terraform import: adopt one existing object under one state owner",
    "Treat import as a transfer of management, not a safe-plan shortcut.",
    "An import block maps an existing remote object to a Terraform resource address. It does not create a complete, correct configuration for that object, nor does it settle which team owns future edits. Once an object is represented in state, later plans can propose changes or destruction. Import succeeds only when the intended address, provider identity, remote identifier, configuration, and operational owner all refer to the same object.",
    "A receipt archive bucket was created manually during an outage. First record its account, region, name, encryption, retention, access policy, replication, and current owner. Check every known state and automation path for an existing manager; importing the same bucket into two states creates competing writers. Write the resource configuration to match the approved live settings, then add the import mapping shown below. Run a plan in a controlled workspace and inspect the import action plus every subsequent update or replacement. A post-import plan proposing to relax retention is a configuration mismatch, not a harmless import detail. Test with a disposable bucket before touching the live one. After application, run a fresh plan and confirm no unexplained changes, then retire the manual change path so the next operator does not edit the bucket outside the new owner.",
    "hcl", 'import {\n  to = aws_s3_bucket.receipt_archive\n  id = "receipt-archive-prod"\n}\n\nresource "aws_s3_bucket" "receipt_archive" {\n  bucket = "receipt-archive-prod"\n}',
    "Import reads remote attributes and writes state; the immediate API and storage cost is usually small compared with the risk of a later incorrect plan. Some resources require related policies, access rules, or subresources to be modeled separately, which expands review time. A single import can therefore create several follow-up ownership tasks. Measure unexplained drift after import, competing automation writes, and the count of objects whose live settings lack a declared owner. Do not use plan success as proof that the archive remains compliant.",
    ["Do not import one remote object into two active states.", "Do not accept generated configuration without reviewing retention and security arguments.", "Do not assume an import action proves the next plan is a no-op."],
    ["devops/terraform-state-and-plan", "devops/infrastructure-drift-triage", "devops/terraform-address-refactoring", "devops/ambiguous-cloud-create-reconcile"],
)

lesson(
    "terraform-replacement-headroom", "Terraform replacement: prove old and new can coexist",
    "Budget names, quota, data movement, and cutover time before create-before-destroy.",
    "Some remote properties cannot change in place. Terraform then plans to replace the object. The create-before-destroy lifecycle rule changes operation order, but it cannot make a unique name reusable while the old object exists or grant extra provider quota. It may also affect dependencies. A replacement review must identify the actual coexistence requirement and the user-facing handover, not stop at the plan symbol indicating a replacement.",
    "A receipt worker pool needs a launch-template change. In an isolated environment, plan the replacement and list every new instance, address, disk, and dependent object that must exist while the old pool serves traffic. Reserve quota for overlap, use distinct names where required, and verify readiness before redirecting work. The fragment is only an operation-order rule; the deployment still needs a data and traffic migration. If the object is a stateful database, decide whether replication, snapshot restore, or a maintenance window is needed before selecting the rule. Simulate failure after creation but before old-resource deletion and record how to identify and retire the stray replacement. Compare the final plan with actual provider inventory after apply. A prevent-destroy guard can block an accidental replacement while present, but removing that resource block removes the guard's protection.",
    "hcl", 'resource "aws_autoscaling_group" "receipt_workers" {\n  name_prefix         = "receipt-workers-"\n  max_size            = 6\n  min_size            = 3\n  desired_capacity    = 3\n  vpc_zone_identifier = var.worker_subnet_ids\n\n  lifecycle {\n    create_before_destroy = true\n  }\n}',
    "Overlap can temporarily double compute, addresses, volume attachments, and load on a shared database. Quota requests and data synchronization may take longer than the apply itself. Destroy-first avoids overlap but can create downtime; create-first reduces that window only when both generations can coexist and cutover is verified. Track peak resource count, ready capacity, old-generation traffic, and orphan count. A low-cost test should deliberately exhaust one quota to prove the rollback path retains the old generation.",
    ["Do not assume create-before-destroy solves a globally unique name conflict.", "Do not rely on prevent-destroy after removing the resource block.", "Do not mark the replacement complete before traffic and data have moved."],
    ["devops/terraform-state-and-plan", "devops/provider-quota-preflight", "devops/graceful-pod-shutdown", "devops/rollback-image-retention"],
)

lesson(
    "terraform-state-lock-recovery", "Terraform state locks: distinguish a stale lease from an active writer",
    "Recover only the failed operation's own lock after proving no writer remains.",
    "A supported Terraform backend may lock state during operations that could write it. The lock prevents two runs from racing to publish incompatible state snapshots. A failed runner can leave a lock that needs recovery, but an operator who clears a live writer's lock creates the same concurrency hazard the backend was meant to prevent. Lock handling depends on the backend; a visible lock error alone does not establish that the lock is stale.",
    "A production plan reports a lock ID after a CI runner disappears. Stop scheduled applies for that workspace, identify the lock owner and operation, check the runner and provider activity, and confirm whether a state write finished. Preserve the current state version and remote change record before taking action. Only the team that owns the failed operation should use the lock ID to release its own abandoned lock; the command below is an example of the final recovery step, not a first response. Replan after unlock and compare the new plan with the failed run's last known actions. If remote infrastructure changed but state did not, reconcile that object before any new apply. Alert on lock age, queue length, and repeated recovery requests, while keeping planned long operations from being mistaken for failures.",
    "bash", 'terraform force-unlock "6b8c1c29-4f71-42a0-bc53-79c70ab5d541"',
    "A lock serializes writers and can delay deployments during a long apply. That wait is cheaper than repairing divergent state, which can involve manual remote inventory and data risk. Disabling locking to save minutes removes the single-writer guarantee. Force-unlock itself does not alter infrastructure, but the next writer can if the previous one was still running. Measure how long the stale lock blocked releases and whether a new plan reveals incomplete remote effects before declaring recovery complete.",
    ["Do not run with locking disabled merely to bypass a busy workspace.", "Do not unlock another operator's active run.", "Do not resume an apply before checking whether the failed run changed remote objects."],
    ["devops/terraform-state-and-plan", "devops/ambiguous-cloud-create-reconcile", "devops/infrastructure-drift-triage", "devops/git-change-control"],
)

lesson(
    "terraform-state-secret-boundary", "Terraform state secrets: redaction is not removal",
    "Protect state snapshots and saved plans as sensitive artifacts.",
    "Marking a Terraform input or output sensitive hides its value from ordinary command display. It does not generally remove the value from state or a saved plan. The backend, runner disk, artifact store, and anyone who can read snapshots may therefore gain access to credentials or private configuration. Avoiding a value in console output is a presentation control; containing or omitting it from persistent artifacts is a separate design decision.",
    "A receipt service bootstrap uses a database password. Trace where that password enters the run: CI secret store, environment, provider request, plan file, state snapshot, logs, support bundle, and backup. Restrict backend read and write roles separately, encrypt stored state and backup copies, set short retention for saved plans, and avoid attaching plan binaries to broad-access tickets. The fragment shows a sensitive variable for output redaction; it is not a promise that state is secret-free. If the supported Terraform version and provider allow an ephemeral input or write-only argument for this exact use, test that path with a disposable credential and inspect both plan and state. Rotate a test password, then verify old state versions and backup policies account for the retired value. Redact values from diagnostics before sharing an incident record.",
    "hcl", 'variable "receipt_db_password" {\n  type      = string\n  sensitive = true\n}',
    "Encryption and narrow access add key-management and audit overhead, but keeping saved plans indefinitely grows the exposure window. A remote backend may charge for state versions, encryption operations, and access logs. Removing a secret from current configuration does not delete it from old snapshots. Count principals with state-read rights, plan artifact lifetime, successful access reviews, and rotation completion across retained copies. The best reduction is to keep the credential out of Terraform-managed attributes where the provider and workflow permit it.",
    ["Do not commit state or saved plan files to source control.", "Do not treat a sensitive flag as state encryption or omission.", "Do not paste raw plan JSON into a widely shared ticket."],
    ["devops/terraform-state-and-plan", "devops/secret-rotation-rollout", "devops/ci-oidc-claim-boundary", "devops/supply-chain-verification"],
)

lesson(
    "terraform-for-each-key-identity", "Terraform collection keys: keep resource identity stable through reorderings",
    "Choose durable business keys before expanding one block into many instances.",
    "Terraform addresses every instance created by for_each using its map or set key. A key is part of resource identity in state, so changing it can appear as a removal and a creation even when the intended remote object is unchanged. The collection keys must be known before remote actions. By contrast, count uses numeric indexes: inserting one item near the front of an ordered list can shift several addresses and produce noisy or dangerous plans.",
    "A receipt platform has worker groups for eastern and western regions. Model each with a stable region code as the map key, then review a plan after reordering the source declaration: it should not replace groups simply because the file order changed. The fragment uses a map of approved group sizes; in a complete module, each key feeds a resource that has unique names and subnet choices. Do not derive the key from a provider-generated ID that is unknown until apply, and do not place secret data in keys because addresses appear in output and state metadata. When a business key genuinely changes, write an explicit state address move and inspect the resulting plan before apply. Test additions, deletions, and renames separately; a rename may require a remote rename or replacement even when the state address is moved.",
    "hcl", 'locals {\n  receipt_worker_groups = {\n    "region-east" = 3\n    "region-west" = 2\n  }\n}\n\nresource "terraform_data" "worker_group_contract" {\n  for_each = local.receipt_worker_groups\n  input = {\n    region_code = each.key\n    target_size = each.value\n  }\n}',
    "A stable key prevents address churn, but it does not make provider updates free. Each instance still incurs refresh and possible API calls, and a large collection expands plan size roughly with instance count. Key design also creates migration cost if a team later changes its naming scheme. Measure planned creates and destroys after each collection edit, not just total instance count. Prefer a key based on a durable identifier that operators can recognize during incident response.",
    ["Do not use a provider-generated ID as a for_each key before it exists.", "Do not put credentials or private customer fields in instance keys.", "Do not equate an address move with a remote rename."],
    ["devops/terraform-address-refactoring", "devops/terraform-module-contracts", "devops/terraform-state-and-plan", "devops/ephemeral-environment-controls"],
)

lesson(
    "terraform-ignore-changes-contract", "Terraform ignore_changes: name the second owner of every ignored field",
    "Ignore only attributes whose updates belong to another controlled process.",
    "The ignore_changes lifecycle rule tells Terraform not to plan updates for selected existing-resource attributes, though those arguments still matter during creation. It can reduce a fight with an autoscaler or another controller, but it can also hide an unauthorized edit. An ignored field needs an explicit owner, a desired range, an independent drift signal, and a procedure for returning control to Terraform. Otherwise a clean plan becomes false reassurance.",
    "A receipt worker pool is scaled by an autoscaling controller. Terraform creates the pool with a starting desired capacity, but the controller adjusts that value while traffic changes. The fragment limits the exception to desired_capacity; other pool settings remain managed by Terraform. Record the controller identity, permitted bounds, emergency override path, and the metric that catches capacity outside the contract. In a test environment, change desired capacity through the controller and confirm Terraform does not fight it. Then change an unrelated security setting outside Terraform and confirm the plan still proposes correction. Also simulate the controller being disabled: the ignored capacity can remain wrong without a Terraform diff, so alert from observed capacity and SLOs. Review every ignore rule when ownership changes, and remove it with a planned handover rather than silently adding more ignored fields.",
    "hcl", 'resource "aws_autoscaling_group" "receipt_workers" {\n  name_prefix         = "receipt-workers-"\n  max_size            = 8\n  min_size            = 2\n  desired_capacity    = 3\n  vpc_zone_identifier = var.worker_subnet_ids\n\n  lifecycle {\n    ignore_changes = [desired_capacity]\n  }\n}',
    "Ignoring one attribute reduces noisy plans and needless API writes. The cost is a second control loop and separate monitoring. Ignoring all attributes can make the plan nearly useless for detecting unauthorized updates, while leaving the team responsible for their effects. Measure controller changes, capacity outside declared bounds, and time since the last ownership review. A nightly drift report must compare actual values with the external owner's contract, not rely solely on Terraform's no-op result.",
    ["Do not ignore an entire resource to silence a recurring drift alert.", "Do not leave an ignored field without a named controller and alert.", "Do not assume ignore_changes prevents Terraform from using the value on creation."],
    ["devops/infrastructure-drift-triage", "devops/terraform-state-and-plan", "devops/horizontal-autoscaling", "devops/terraform-replacement-headroom"],
)

lesson(
    "terraform-state-removal-handoff", "Terraform state removal: hand off an object without deleting it",
    "Separate release of management from destruction of infrastructure.",
    "Deleting a Terraform resource block usually plans to destroy the remote object still recorded in state. If another team or tool must take ownership while the object remains, the exit needs an explicit state-removal action. A removed block with destroy set to false expresses that intent in configuration. It does not transfer policy, credentials, monitoring, or backup responsibility by itself; the receiving owner must be ready before the old state stops managing the object.",
    "A central platform team takes over an archive bucket used by a receipt service. Before removing the old resource block, record the bucket identifier, region, policies, retention, backup, alerts, and the new team's state address or management system. Freeze edits during the handoff. Replace the old resource declaration with the reviewed removed block below, plan and confirm it says the object will be forgotten without remote deletion, then apply under the state lock. The receiving owner adopts the object, runs a no-op plan or equivalent inventory check, and verifies that old automation no longer writes it. Keep the handoff record and a safe recovery path in case neither manager sees the object. Do not run both writers while they each believe they are authoritative. Test the procedure on a disposable bucket, including a failed receiving import, before scheduling a production handoff.",
    "hcl", 'removed {\n  from = aws_s3_bucket.receipt_archive\n\n  lifecycle {\n    destroy = false\n  }\n}',
    "Removing an address reduces the old state's scope but creates a short period in which the object may have no active configuration owner. Coordinated freeze time and duplicate inventory checks cost more than a direct delete, but they prevent accidental data loss. State snapshots can still contain historical attributes after removal, so retention and access policy remain relevant. Measure orphaned objects, overlapping writers, and time between old-owner release and new-owner adoption. If the plan contains destruction, stop and correct it before apply.",
    ["Do not delete the resource block and assume the remote object will remain.", "Do not release the old owner before the receiver can adopt the object.", "Do not forget historical state copies when transferring sensitive infrastructure."],
    ["devops/terraform-import-ownership", "devops/terraform-address-refactoring", "devops/terraform-state-secret-boundary", "devops/terraform-state-and-plan"],
)

titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/terraform-ownership-handoff-project"
quiz_path = "quizzes/devops-terraform-ownership-decisions"
titles[project_path] = "Project: hand off Terraform-managed infrastructure without a replacement surprise"
titles[quiz_path] = "DevOps Terraform ownership decisions"
unknown = {path for item in specs for path in item["related"] if path not in titles}
assert not unknown, unknown


def links(paths):
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in paths
    ) + "</ul>"


for heading, summary, slugs in [
    ("Dependency and adoption integrity", "Pin executable dependencies and adopt existing objects under one owner.", ["terraform-provider-lock-integrity", "terraform-import-ownership"]),
    ("Replacement and lock recovery", "Check coexistence capacity and recover state only after the writer stops.", ["terraform-replacement-headroom", "terraform-state-lock-recovery"]),
    ("State secrecy and instance identity", "Control sensitive artifacts and keep collection keys stable.", ["terraform-state-secret-boundary", "terraform-for-each-key-identity"]),
    ("Shared control and handoff", "Name the owner of ignored fields and remove state addresses deliberately.", ["terraform-ignore-changes-contract", "terraform-state-removal-handoff"]),
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
               sort_order=20400 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
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
               summary="Rehearse import, replacement, lock recovery, secret handling, and ownership transfer.",
               difficulty="Advanced", sort_order=20490,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 9,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in project_related]}
project["body"] = (
    "<p>Build an isolated receipt environment with a disposable archive, two worker groups, a remote state backend that supports locking, and a second configuration representing a receiving team. Use synthetic credentials. Record provider and module versions, lock-file changes, current state addresses, object inventory, expected owner, and a baseline plan before each phase. A test passes on observed state and remote objects, not a successful command exit alone.</p>"
    "<h2>Adopt and replace</h2><p>Create the archive outside Terraform, then import it under exactly one state address. Compare configuration with encryption, retention, and access settings; reject a post-import plan that changes them unexpectedly. Reorder the worker-group map and confirm stable instance addresses. Rename one key with a reviewed address move, then test a provider upgrade separately from the module version change. Trigger a worker replacement with quota for overlap, observe both generations, and prove traffic moves before old capacity disappears. Repeat with insufficient quota and verify the old generation remains available.</p>"
    "<pre><code class=\"language-text\">Receipt infrastructure acceptance gates\nProvider: selected version and package checksums reviewed\nModule: exact approved version recorded separately\nImport: one object, one active state owner, no surprise update\nReplacement: quota, names, traffic, and rollback proven\nLock: abandoned writer verified before own lock is released\nSecrets: saved plan and state readers audited\nKeys: reordered map produces no address churn\nIgnored field: external controller and alert named\nHandoff: old state forgets object; receiving owner adopts it</code></pre>"
    "<h2>Recover and transfer</h2><p>Interrupt a test run while it holds the state lock. Verify the runner has stopped, preserve state, release only that run's abandoned lock, and replan against remote inventory. Inspect a saved plan and state snapshot for the synthetic credential; tighten access and retention before continuing. Let an autoscaler change only the worker group's desired capacity, then show that an unrelated security change still appears in the plan. Finally transfer the archive to the receiving configuration with an explicit state-removal plan, a freeze, and an adoption check. Abort if either configuration plans destruction or both claim the same object.</p>"
    "<h2>Cost and verification</h2><p>Measure peak overlap capacity, state lock wait, provider refresh time, snapshot retention, and the gap between old-owner release and new-owner adoption. A cleaner plan is not enough: confirm actual object policy, customer traffic, and owner inventory. Record who can read state, who can apply it, and how a failed handoff is reversed without creating a second writer.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not use a provider lock file as evidence that modules are pinned.</li><li>Do not force-unlock an active run.</li><li>Do not delete a resource block when the intent is to keep its object.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*project_related, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Terraform ownership handoff drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("What does the Terraform dependency lock file currently record?", ["Provider selections and package checksums", "All remote module version selections", "Cloud object retention policies"], "Remote modules need their own version constraints."),
    ("How should a team keep one remote module release fixed?", ["Use an exact approved module version", "Rely only on the provider lock file", "Remove every module constraint"], "The provider lock file does not freeze remote module selection."),
    ("What is the first ownership check before importing a live bucket?", ["Ensure no other active state already manages it", "Delete its encryption policy", "Skip the post-import plan"], "Two active states create competing managers."),
    ("What can happen after an import block is applied?", ["A later plan may propose changes from configuration mismatch", "The object can never be replaced", "The plan must always be empty"], "Import adopts state; it does not guarantee configuration parity."),
    ("What can block create-before-destroy even when the plan selects it?", ["A unique name or insufficient quota", "A committed provider lock file", "A stable for_each key"], "Both generations must coexist before the old one is removed."),
    ("When is force-unlock appropriate?", ["After proving the team's own locked operation stopped", "Whenever another team runs slowly", "To avoid inspecting remote changes"], "Removing a live lock can permit concurrent state writers."),
    ("What does sensitive = true fail to guarantee?", ["Omission of the value from state and saved plans", "Redaction in normal CLI presentation", "A declaration that the input is sensitive"], "Display redaction is separate from persistent storage."),
    ("Why use stable map keys with for_each?", ["They preserve instance addresses when declaration order changes", "They eliminate remote API costs", "They allow unknown keys at apply time"], "The key forms part of each instance address."),
    ("What must accompany an ignored desired-capacity field?", ["A named external owner and independent alert", "A decision to ignore all resource attributes", "A promise Terraform will correct every capacity edit"], "Ignored updates need another control and observability path."),
    ("What happens if a managed resource block is simply removed?", ["Terraform can plan to destroy its remote object", "State automatically transfers to a new team", "Its credentials are removed from every backup"], "Deletion from configuration is not a management handoff."),
    ("Which removed-block setting keeps the remote object?", ["destroy = false", "destroy = true", "prevent_destroy = false"], "The state address is forgotten while the object remains."),
    ("What proves a state handoff is finished?", ["The receiving owner adopts and verifies the object after old ownership ends", "Only the old plan is green", "Both configurations continue applying to the same object"], "An explicit receiver and no overlapping writers complete the transfer."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on Terraform dependencies, state, and handoff.",
            sort_order=20500, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in project_related],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Choose the state and ownership boundary that preserves the intended remote object. Check a plan against actual inventory, backend access, and the receiving team's run before approving a handoff.</p>"
    "<h2>Review these lessons</h2>" + links(project_related)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-service-traffic-decisions", "quizzes/devops-data-continuity-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not infer module pinning from a provider lock.</li><li>Do not treat a state removal as automatic transfer of operations.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Terraform ownership check</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": path, "title": titles[path]} for path in [project_path, quiz_path])

for source, targets in {
    "devops/terraform-state-and-plan": ["devops/terraform-provider-lock-integrity", "devops/terraform-state-lock-recovery", "devops/terraform-state-secret-boundary"],
    "devops/terraform-module-contracts": ["devops/terraform-provider-lock-integrity"],
    "devops/terraform-address-refactoring": ["devops/terraform-for-each-key-identity", "devops/terraform-state-removal-handoff"],
    "devops/infrastructure-drift-triage": ["devops/terraform-import-ownership", "devops/terraform-ignore-changes-contract"],
    "devops/provider-quota-preflight": ["devops/terraform-replacement-headroom"],
    "devops/ambiguous-cloud-create-reconcile": ["devops/terraform-import-ownership", "devops/terraform-state-lock-recovery"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Advanced follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1, "total_records": len(rows)}))
