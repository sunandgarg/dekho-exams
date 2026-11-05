"""Add original Linux host change and access lessons to the DevOps curriculum."""

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
project_hub = "devops/devops-tutorial/project"
quiz_hub = "devops/quizzes"
project_path = "devops/linux-host-change-fault-drill-project"
quiz_path = "quizzes/devops-linux-host-change-decisions"


def lesson(slug, title, summary, definition, decision, sample, language, cost, mistakes, related):
    return dict(path="devops/" + slug, title=title, summary=summary,
                definition=definition, decision=decision, sample=sample,
                language=language, cost=cost, mistakes=mistakes, related=related)


specs = [
    lesson(
        "linux-kernel-reboot-cohort",
        "Linux kernel rollouts: prove the running kernel after each reboot cohort",
        "An installed kernel package is not the kernel that currently serves traffic.",
        "A kernel rollout has three states: the package available on disk, the boot entry selected for the next start, and the kernel running now. Only the last state proves the host crossed the reboot boundary. A live patch can alter selected running functions without a reboot, but its coverage is narrower than replacing the running kernel and it does not remove the need to plan later boot transitions. Treat a fleet patch as a sequence of host cohorts with a maximum unavailable count, health gates, and a known prior boot entry. Preserve the exact package and bootloader state before changing either.",
        "A 93-node API fleet needs a kernel security update. The operator drains one canary node, records its current release and boot entry, installs the approved package, and reboots it through the normal maintenance path. After boot, they compare uname output with the approved release, check failed units, mount and network state, and run a synthetic API write through the load balancer before admitting traffic. A second cohort of five starts only after the canary remains healthy for an observation period. If the new kernel fails before remote access returns, a console or provider rescue path selects the retained prior entry. If the host boots but the API path fails, rollback includes draining it again and proving the earlier kernel actually runs after reboot.",
        "uname -r\ncat /proc/cmdline\nsystemctl --failed",
        "bash",
        "Serial cohorts extend the maintenance window, but a fleet-wide reboot risks losing all replicas to the same driver or boot error. Measure time from drain to application acceptance, count hosts running the intended release, and alert on a host stuck between installed and running versions. Rollback is not a package-manager command alone; the selected boot entry and service health must be checked again. Keep workload quorum and capacity margins during each cohort. If the service has local state, confirm its shutdown and replay contract before draining.",
        ["Do not mark a host patched because a package manager returned success.", "Do not assume a live patch covers every kernel change or survives an unrelated reboot plan.", "Do not delete the earlier boot entry before the canary and recovery path are proven."],
        ["devops/dependency-patch-campaign", "devops/connection-drain-boundary", "devops/linux-service-diagnostics"],
    ),
    lesson(
        "ssh-host-key-rotation",
        "SSH host-key rotation: change server identity without teaching clients to ignore warnings",
        "The host key authenticates the server; it is separate from the user's login key.",
        "An SSH client records or otherwise trusts a server host key, then rejects an unexpected identity on a later connection. A planned rotation therefore needs an independently verified replacement fingerprint and a client migration path. OpenSSH can present multiple host keys during an overlap. Where the client and trust configuration support it, UpdateHostKeys can learn additional keys after a connection authenticated with an already trusted plain host key. That mechanism has conditions and is not a universal distribution channel. Inventory automated clients, pinned known-host files, host certificates, and image rebuilds before removing the old key.",
        "A build-runner fleet reaches a source mirror over SSH. Operators generate a new Ed25519 host key on the mirror, record the fingerprint through a trusted inventory channel, and configure both old and new host keys during a bounded overlap. They connect from a canary runner with strict host checking, verify the server presents the expected identity, and inspect whether its client configuration learned the additional key. Runners using centrally managed known-host files receive an explicit updated trust bundle instead. Only after every runner cohort can connect under strict checking do operators remove the old host key. A surprise key change pauses deployment until the mirror identity is investigated; deleting known_hosts entries is not a verification step.",
        "ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub\nsshd -t",
        "bash",
        "Overlap preserves continuity but temporarily keeps the old private key usable, so the deadline must be short if it may be exposed. Distributing a new trust bundle consumes coordination across CI runners, human clients, and recovery consoles. Count clients that still trust only the retiring key and test an actual strict-check connection from each client class. A host certificate design can reduce per-host pinning work, but moves trust to a certificate authority and its signing controls. Record whether the rotation is planned or a suspected compromise; the latter changes the containment sequence.",
        ["Do not set StrictHostKeyChecking to no to make a rotation pass.", "Do not confuse the server host key with a user's authorized key.", "Do not assume UpdateHostKeys works with every custom known-hosts configuration."],
        ["devops/credential-incident-rotation", "devops/self-hosted-runner-isolation", "devops/break-glass-access"],
    ),
    lesson(
        "ssh-user-certificate-expiry",
        "SSH user certificates: bind host login to an expiry and a narrow principal",
        "A short-lived SSH certificate is useful only when the server checks who it represents.",
        "An SSH user certificate signs a user's public key with a trusted user CA and carries validity bounds and principals. A server configured with TrustedUserCAKeys can accept that CA, while its authorized-principals policy determines which certificate principal may enter a target account. Without an explicit principals file, the target username normally supplies the accepted principal. This narrows the useful life of a stolen certificate, but it does not revoke the user's private key elsewhere or remove sessions that are already open. The issuing service needs identity verification, clock health, audit records, and an emergency removal path for the CA or a compromised signer.",
        "A database responder requests a certificate valid for 27 minutes with the principal db-operator. The bastion maps that principal only to a dedicated maintenance account, denies shell access to the service account, and records the certificate key ID with the ticket ID. A disposable host test tries a valid certificate, an expired one, and the same certificate against an account whose principal mapping does not match. The rollout retains a separately controlled break-glass route in case the issuer is unavailable. After expiry, a fresh login must fail; an already established session is handled through a separate incident procedure when immediate eviction is required.",
        "TrustedUserCAKeys /etc/ssh/trust/people_ca.pub\nAuthorizedPrincipalsFile /etc/ssh/principals/%u\nTicket: CHG-4726\nPrincipal: db-operator\nLifetime: 27 minutes",
        "text",
        "Short validity reduces the replay window but increases reliance on the issuer and accurate clocks. A broad principal accepted by many accounts defeats the intended boundary. Measure issuance latency, denied-login causes, expired-certificate acceptance, and remaining direct authorized_keys entries that bypass the certificate path. Test the effective sshd configuration and a real negative login on a disposable host before replacing an existing access system. A CA key held on the same general-purpose host as its issuer creates a different compromise scope than a protected signer.",
        ["Do not use a certificate principal that grants every host account.", "Do not claim expiry terminates sessions already established.", "Do not remove the emergency access path before the issuer failure drill."],
        ["devops/break-glass-access", "devops/clock-skew-operational-check", "devops/federated-workload-identity"],
    ),
    lesson(
        "sudo-command-boundary",
        "sudo policy: authorize an exact maintenance action, not a path to a shell",
        "A sudo rule grants a command execution boundary that may be wider than its line suggests.",
        "sudoers can constrain the invoking user, target identity, executable path, and command arguments. A wildcard argument, editor, pager, interpreter, or script writable by the caller may let the user escape into another command. The rule also depends on environment handling and executable integrity. A safe maintenance workflow prefers a small root-owned helper that validates inputs and performs one narrow operation, while the policy allows only that helper under the required identity. Exact path matching does not prove that a mutable program or its imported files are safe. Review the effective policy for the actual operator identity and group memberships.",
        "A search-index responder needs to rotate one local service log, not administer the entire host. Instead of giving sudo access to a shell, text editor, or arbitrary systemctl arguments, the team creates a root-owned helper that accepts the fixed service name, checks the log destination, and records the ticket ID. The sudo rule grants that helper to the responder group. On a disposable host, testers try the approved invocation, an extra argument, a service-name substitution, a writable helper replacement, and a pager or environment escape. Each unauthorized path must fail while the approved operation succeeds. The rule and helper are versioned together so review sees the full authority being granted.",
        "Allowed action: /usr/local/sbin/rotate-search-index-log\nTarget identity: root\nCaller group: search-responders\nRejected: arbitrary unit name, shell, editor, extra arguments\nEvidence: sudo -l, visudo -c, allowed and denied probes",
        "text",
        "A narrow helper adds a small amount of maintained code, but reduces the incident scope of a stolen operator credential. A single broad sudo rule is cheaper to write and much more expensive to audit or contain. Record accepted and rejected probes in CI or a disposable host, then re-run them when the helper or its dependencies change. Capture sudo's command log without writing credentials or sensitive payloads into arguments. If the operation itself allows user-controlled file paths, root ownership of the helper does not make the input safe.",
        ["Do not grant a general shell to avoid writing a constrained maintenance action.", "Do not trust exact executable paths when the file or its imports are operator-writable.", "Do not assume an editor or pager is a read-only command under sudo."],
        ["devops/break-glass-access", "devops/cloud-policy-decision-trace", "devops/audit-data-event-coverage"],
    ),
    lesson(
        "nftables-remote-change-rollback",
        "nftables rollouts: apply a checked ruleset with an access recovery timer",
        "An atomic firewall transaction can still atomically lock the operator out.",
        "nftables can load a file of rule commands as one transaction, so a complete replacement avoids a long intermediate state with only half the rules present. A syntax check catches malformed rules but cannot prove that the management subnet, IPv6 path, established connections, or service probes remain permitted. A remote change therefore needs an out-of-band console or a timed rollback mechanism that restores a known-good ruleset unless a separate post-change confirmation cancels it. The active ruleset and boot-persistent configuration must also agree, or a reboot can undo the observed result.",
        "A 47-host edge pool limits management SSH to a bastion network. Operators stage the candidate file, validate its syntax, preserve the current ruleset, and arm a rollback from outside the SSH session. They apply to one canary through a console-capable path. An independent probe checks new and established bastion sessions, public application traffic, and IPv6. The confirmation system cancels rollback only after those probes pass. When an injected rule drops the bastion's source subnet, the timer restores the prior ruleset without requiring the broken SSH channel. The cohort advances only when the canary survives a reboot with the intended persistent ruleset.",
        "nft -c -f /etc/nftables/candidate.nft\nnft list ruleset",
        "bash",
        "A rollback timer reserves a brief period when the new rule may be active before recovery, so choose its interval from measured probe latency and business impact. A permissive fail-open rollback can reintroduce a known exposure; the incident owner must compare that risk with loss of access and use the console path if necessary. Test both IPv4 and IPv6, as an IPv4-only success hides a separate path. Record the committed ruleset hash and the boot file hash. Repeated ad hoc changes that are not written to the persistent file create a false sense of safety until the next restart.",
        ["Do not equate nft syntax success with reachable management access.", "Do not run a remote deny rule without a tested console or rollback path.", "Do not forget IPv6 and boot persistence when confirming the change."],
        ["devops/network-path-diagnosis-project", "devops/connection-drain-boundary", "devops/host-protocol-failure-project"],
    ),
    lesson(
        "luks-recovery-key-drill",
        "LUKS recovery drills: preserve independent unlock and header recovery paths",
        "A backup of encrypted bytes is not enough when the only unlock path is lost.",
        "A LUKS volume depends on its encrypted data area, header and keyslots, and at least one valid way to unlock a slot. A header backup can rescue certain metadata damage, but it is sensitive material: together with a passphrase valid when it was made, an older backup may still unlock data after that passphrase is removed from the live header. A header backup does not replace a data backup, and restoring an old header can undo later keyslot changes. Keep recovery credentials and header backups under separate, audited controls. Practice against a copied disposable volume, never the only production disk.",
        "A batch-processing host uses one automated boot unlock path and one sealed recovery passphrase. Before rotating the automated secret, an operator verifies the recovery slot on a cloned encrypted volume and captures a protected header backup. They add and test the new slot, then remove the retiring slot only after a complete reboot of a disposable clone proves the new boot path. A second drill deliberately corrupts the clone's header and restores the matching protected backup, then verifies file hashes from a separate data backup. The drill records who accessed the recovery material, how long the host stayed unavailable, and whether an older header backup could still admit a retired credential.",
        "Volume inventory: batch-worker-root, clone only\nRecovery slot: separate sealed passphrase\nHeader backup: protected and versioned with keyslot changes\nProof: cold unlock, reboot, file-hash comparison\nForbidden test target: sole production copy",
        "text",
        "Independent recovery material costs storage, access review, and periodic testing, but prevents a single broken automation path from stranding an encrypted host. Each header backup increases the set of credentials that may recover old keyslots; destruction and retention therefore belong in the rotation plan. A successful unlock test proves access to a volume, not integrity or completeness of its files. Pair it with a data restore and application-level verification. If the recovery passphrase is stored in the same inaccessible volume, the apparent second path is circular.",
        ["Do not restore an old header onto the sole production volume as a practice test.", "Do not treat a header backup as a backup of application data.", "Do not forget that an old header backup can preserve access for a retired passphrase."],
        ["devops/secret-rotation-rollout", "devops/recovery-drill-evidence-reset", "devops/break-glass-access"],
    ),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({item["path"]: item["title"] for item in specs})
titles[project_path] = "Linux host change drill: reboot, access, firewall, and disk recovery"
titles[quiz_path] = "Linux host change decisions: access and recovery quiz"
assert all(item["path"] not in by_path for item in specs)
assert project_path not in by_path and quiz_path not in by_path
assert all(target in titles for item in specs for target in item["related"])


def links(paths):
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in dict.fromkeys(paths)
    ) + "</ul>"


related_paths = [item["path"] for item in specs]
for heading, summary, paths in [
    ("Linux host change safety", "Stage kernel reboots, SSH identity, and expiring login authority.", related_paths[:3]),
    ("Linux host recovery boundaries", "Constrain sudo, stage firewall rules, and rehearse encrypted-disk unlock.", related_paths[3:]),
]:
    by_path[course]["data"]["modules"].append({"title": heading, "summary": summary, "lessons": paths})
    by_path[course]["body"] += f"<h2>{html.escape(heading)}</h2><p>{html.escape(summary)}</p>" + links(paths)
by_path[course]["updated_at"] = stamp

for index, item in enumerate(specs):
    path = item["path"]
    row = copy.deepcopy(by_path["devops/continuous-integration"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
               title=item["title"], summary=item["summary"], subject="devops",
               category="DevOps", difficulty="Advanced", tags=["devops", "linux", "host-security"],
               sort_order=26310 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"kind": "tutorial", "reading_minutes": 7,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": course, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in [*item["related"], project_path, quiz_path]]}
    row["body"] = (
        f"<p>{html.escape(item['definition'])}</p><h2>Operational decision</h2>"
        f"<p>{html.escape(item['decision'])}</p>"
        f'<pre><code class="language-{item["language"]}">{html.escape(item["sample"])}</code></pre>'
        f"<h2>Cost and verification</h2><p>{html.escape(item['cost'])}</p>"
        + "<h3>Common Mistakes</h3><ul>"
        + "".join(f"<li>{html.escape(mistake)}</li>" for mistake in item["mistakes"])
        + "</ul><h2>Connected lessons</h2>" + links([course, *item["related"], *related_paths[:2]])
        + "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    )
    rows.append(row)

project = copy.deepcopy(by_path["devops/practice-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title=titles[project_path],
               summary="Fault-test a disposable Linux host across kernel, SSH, sudo, nftables, and LUKS changes.",
               difficulty="Advanced", sort_order=26390,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 13,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in related_paths]}
project["body"] = (
    "<p>Use disposable Linux virtual machines with console access, a simulated bastion, a synthetic API, and a cloned encrypted volume. Version-control the host configuration and keep an external ledger of expected and observed states. Use dedicated test identities and test data. The exercise is complete only when a failed change can be reversed without relying on the access path that it broke.</p>"
    "<h2>Stage the reboot boundary</h2><p>Record the running kernel, installed candidate, selected boot entry, API acceptance, and spare capacity. Drain one canary, reboot into the approved kernel, and check a synthetic write before returning it to service. Inject a boot failure on a clone and select the retained prior entry from the console. Repeat in a five-host cohort while preserving workload quorum. A package-install receipt without a new running kernel fails this gate.</p>"
    "<h2>Challenge every access path</h2><p>Rotate the bastion's SSH host key with an overlap and a fingerprint distributed through trusted inventory. Prove strict-check connections work for managed and ordinary clients; an unexpected fingerprint must stop the change. Issue one 27-minute user certificate for a narrow principal and reject an expired certificate and a wrong-account login. Allow a responder to run one root-owned maintenance helper through sudo, then reject a substituted service name, an added argument, and an operator-writable helper.</p>"
    "<pre><code class=\"language-text\">Acceptance ledger\nKernel: approved running release after reboot; prior entry bootable\nSSH server: fingerprint verified; strict clients connect; old key removed after overlap\nSSH user: db-operator principal accepted only for maintenance account\nSudo: one helper accepted; shell, extra arguments, and writable replacement denied\nFirewall: independent probes pass; bad rule triggers timed restore\nLUKS: cloned volume unlocks with recovery path and matching header backup</code></pre>"
    "<h2>Recover the network and disk</h2><p>Load a checked nftables candidate on a canary only after arming a timed restore from outside the SSH session. Inject a rule that blocks the bastion subnet and observe automatic recovery. Confirm the persistent ruleset survives reboot and that IPv6 was tested. On the cloned LUKS volume, rotate an unlock slot, prove cold boot recovery, then simulate header damage and restore a protected matching backup. Verify file hashes from an independent data backup; unlocking alone is not the completion signal.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not run the recovery drill against the only copy of production data.</li><li>Do not let the same SSH session be the sole path to reversing its own firewall rule.</li><li>Do not count a configuration check as a successful login, reboot, or restore.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*related_paths, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Linux host change drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("What proves a kernel update has crossed the reboot boundary?", ["The running release matches the approved target", "The package was downloaded", "A livepatch package exists"], "Installation and running state are different."),
    ("What should a kernel canary prove before fleet expansion?", ["Boot health and a real application path", "Only a successful package command", "Only an empty package queue"], "An application check catches failures beyond boot."),
    ("Whose identity does an SSH host key authenticate?", ["The server", "The human operator", "The sudo target account"], "The client uses the host key to check its server."),
    ("How should clients handle an unexpected SSH host-key change?", ["Stop and verify through an independent channel", "Disable strict checking", "Delete every known-host entry"], "A warning may indicate a different or compromised server."),
    ("What limits the usefulness of a short-lived SSH user certificate?", ["Its validity bounds plus server-side principal checks", "A broad shared principal", "A disabled host-key check"], "Time and account mapping work together."),
    ("Does certificate expiry close an existing SSH session?", ["No; established sessions need a separate eviction plan", "Yes; the client is always disconnected at expiry", "Only if sudo is enabled"], "Expiry governs authentication of new connections."),
    ("What can make a narrow-looking sudo rule unsafe?", ["A caller-writable helper or a command that can launch a shell", "A root-owned fixed helper", "A denied extra argument"], "The executable and its escape paths are part of the boundary."),
    ("Which sudo test goes beyond syntax?", ["Allowed and denied invocations under the real operator identity", "Reading only the policy filename", "Counting root accounts"], "Effective authority must be probed."),
    ("What does an nftables syntax check fail to prove?", ["That management and application paths remain reachable", "That the file parses", "That a rule command is recognized"], "Reachability needs independent probes."),
    ("What restores access after a bad remote firewall rule?", ["A timed rollback or working out-of-band console", "The broken SSH connection", "A later package update"], "Recovery cannot depend on the blocked path."),
    ("What is missing from a LUKS header backup alone?", ["The encrypted application data and a tested unlock credential", "Header metadata", "Keyslot metadata"], "Header recovery does not replace data recovery."),
    ("Why is an older LUKS header backup sensitive after key rotation?", ["It may still permit a passphrase valid when that backup was made", "It is always safe to publish", "It automatically removes all retired keys"], "Backup retention can preserve old unlock capability."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path],
            summary="Twelve decisions on kernel rollout, SSH identity, sudo authority, firewall recovery, and encrypted disks.",
            sort_order=26400, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in related_paths],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Decide whether a host change is actually running, trusted, and recoverable. A successful command or policy parse is useful evidence, but it is not the final service check.</p>"
    "<h2>Review these lessons</h2>" + links(related_paths)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-systemd-operating-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not use a broken management path as the only rollback channel.</li><li>Do not confuse encrypted-volume unlock with a verified application restore.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Linux host change decisions</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for source, targets in {
    "devops/dependency-patch-campaign": [related_paths[0]],
    "devops/connection-drain-boundary": [related_paths[0], related_paths[4]],
    "devops/credential-incident-rotation": [related_paths[1]],
    "devops/break-glass-access": [related_paths[2], related_paths[3], related_paths[5]],
    "devops/clock-skew-operational-check": [related_paths[2]],
    "devops/network-path-diagnosis-project": [related_paths[4]],
    "devops/recovery-drill-evidence-reset": [related_paths[5], project_path],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Linux host change follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1,
                  "total_records": len(rows)}))
