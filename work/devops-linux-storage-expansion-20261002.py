"""Add original Linux storage operations and recovery lessons."""

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
project_path = "devops/linux-storage-fault-drill-project"
quiz_path = "quizzes/devops-linux-storage-decisions"


def lesson(slug, title, summary, definition, decision, sample, cost, mistakes, related):
    return dict(path="devops/" + slug, title=title, summary=summary,
                definition=definition, decision=decision, sample=sample,
                cost=cost, mistakes=mistakes, related=related)


specs = [
    lesson(
        "linux-disk-space-attribution",
        "Linux disk pressure: explain missing space before deleting application data",
        "A full filesystem is a capacity incident whose owner may be a process, a mount, or an unlinked file.",
        "Filesystem free-block accounting and a walk of visible directory entries answer different questions. df reports the mounted filesystem's space; du sums files it can traverse under a path. If an application keeps a deleted log open, the directory entry disappears while the file's blocks stay allocated until the descriptor closes. Reserved blocks, snapshots, container layers, quotas, and mount boundaries can produce other differences. Inode exhaustion is a separate failure: a filesystem can have free bytes yet refuse to create another file. First identify the filesystem and its workload, then attribute usage by visible data, open unlinked files, and account-level limits.",
        "A ledger API stops accepting writes with 23 GiB apparently free under the operator's home directory. The actual database mount is 99% full. The responder records df for bytes and inodes, confirms the mount source, and compares du only inside that mount so a nested backup mount does not distort totals. They find a deleted 41 GiB audit file still held by the writer process. Rather than killing the database or removing random files, they coordinate a supported log reopen or controlled restart, check the recovery window, and verify free space plus a real write. If the missing space is instead an immutable snapshot, they follow its retention owner and recovery policy before removal.",
        "df -hT /srv/ledger\ndf -i /srv/ledger\nfindmnt /srv/ledger\nlsof +L1",
        "A directory scan can consume I/O and take minutes on a large tree, so run it with a bounded scope during an incident. Reopening a log may briefly interrupt work; deleting files without ownership evidence can destroy recovery material. Track free bytes, free inodes, growth rate, and the oldest recoverable backup. A dashboard that reports only percent used may miss a small absolute reserve on a large volume. The operator should record the file owner, process ID, and expected release of any unlinked blocks before changing process state.",
        ["Do not run du across a different mounted filesystem and compare it with one df row.", "Do not assume deleting an open file releases its blocks immediately.", "Do not erase backups or database files solely to clear an alert."],
        ["devops/inode-exhaustion-recovery", "devops/ephemeral-storage-limit-accounting", "devops/systemd-journal-retention-evidence"],
    ),
    lesson(
        "linux-filesystem-growth-chain",
        "Linux filesystem expansion: follow the block device to the mounted filesystem",
        "Increasing a cloud volume does not automatically increase the filesystem visible to a process.",
        "A storage expansion can cross several layers: provider allocation, partition, encrypted mapping, logical volume, filesystem, mount, and application quota. The order and commands depend on the actual stack. XFS and ext4 have different growth tools and constraints; a filesystem cannot use space its underlying block device has not exposed. A successful provider resize therefore needs a before-and-after map at every layer, a backup or snapshot recovery plan, and an application write test. Avoid copying a device name from a generic runbook: device ordering can change across boots, and growing the wrong layer may leave the intended mount unchanged.",
        "A report service runs on a 164 GiB encrypted logical volume and needs another 87 GiB. The operator records the provider volume ID, stable device identifier, partition table, LUKS mapper, logical-volume extent map, filesystem type, and mount path. They increase the provider allocation in a disposable replica, rescan the block path through the supported platform procedure, then grow each applicable layer in order. After the filesystem-specific growth step, df reports the new capacity at the service mount, not merely at the raw device. The report service writes and reads a synthetic file, and a restore drill confirms that the previous backup still works. The production rollout uses one host cohort at a time.",
        "lsblk -f\nfindmnt /srv/reports\ndf -hT /srv/reports",
        "Online growth avoids a long outage where the filesystem supports it, but it still carries mapping, provider, and human-selection risk. Increasing size may change storage spend immediately while backup windows and restore time rise with data volume. Measure usable capacity at the mount, backup duration, and the service's write success after the operation. A screenshot of a larger provider disk is weak evidence if the mapper or filesystem stayed small. Keep a record of the exact stable identifier and layer sizes so the next operator does not infer the stack from a name such as /dev/sdb.",
        ["Do not treat a larger provider volume as proof the filesystem grew.", "Do not select a block device from its transient kernel name alone.", "Do not run a filesystem growth command before confirming its type and underlying capacity."],
        ["devops/persistent-storage", "devops/volume-snapshot-recovery", "devops/luks-recovery-key-drill"],
    ),
    lesson(
        "linux-filesystem-readonly-recovery",
        "Linux read-only filesystem incidents: preserve evidence before repair",
        "A filesystem that becomes read-only may be protecting data after an I/O or metadata failure.",
        "A failed write can arise from mount options, a block-device error, a full filesystem, or filesystem corruption. The response must distinguish those causes before changing the mount. Kernel logs, the mount's current options, device health, and the application's first failed write form the initial evidence. Filesystem repair tools are type-specific and can modify metadata; running them against a live mounted filesystem can be unsafe or produce invalid findings. ext4 checking and XFS repair follow different procedures, particularly when an XFS log is dirty. Recovery should occur on a detached clone or during a controlled outage with a backup and a tested restore path.",
        "A billing worker receives read-only errors on /srv/billing after a storage-path timeout. The responder fences writes, records the first kernel error and provider volume event, and verifies that its replica has the last committed invoice ID. On a disposable clone, they examine the filesystem type and replay or inspect metadata through the supported procedure, then compare recovered invoice IDs with the application ledger. A remount to read-write is rejected as a first response because it could mask an active device fault. When the real host returns, acceptance requires a successful application write and a second reader's confirmation; a writable mount flag alone is insufficient.",
        "findmnt -no SOURCE,FSTYPE,OPTIONS /srv/billing\njournalctl -k -n 80\nlsblk -f",
        "Stopping writes costs availability but limits further damage while the cause is unknown. Repair can discard or alter metadata, so retain a pre-repair image and record exactly which utility and options were used. A successful filesystem check does not prove application-level consistency across files and database transactions. Measure lost writes, time to restore a healthy writer, and the verified application recovery point. If the underlying device continues returning I/O errors, a repaired filesystem on the same unhealthy path is not an acceptable return to service.",
        ["Do not run a modifying filesystem repair against the mounted live volume.", "Do not use a force-log-clear option as a routine first step.", "Do not equate a read-write mount with recovered application data."],
        ["devops/volume-snapshot-recovery", "devops/recovery-write-gap-ledger", "devops/backup-and-recovery"],
    ),
    lesson(
        "linux-mount-boot-contract",
        "Linux mount boot contracts: prevent a service from writing into an empty mountpoint",
        "A path can exist even when the expected filesystem is absent.",
        "A mount configured as optional may let the host boot when its device is unavailable. That policy is useful for nonessential media, but dangerous for a stateful service that then writes into the bare directory on the root filesystem. An fstab nofail entry changes how the boot target treats the mount; it does not guarantee that every application depending on the path fails closed. The service needs an explicit mount requirement and a startup check that verifies the source or filesystem identity, not merely a directory's existence. For a remote mount, network ordering and timeout behavior must be tested during a cold boot and a later disconnect.",
        "A document index expects a separate volume at /srv/index. The host boots once with that volume missing. The desired behavior is a healthy management plane but no index writer: the service stays stopped, readiness fails, and an alert names the absent mount. Operators inject the missing device on a disposable VM, inspect generated mount units and the index service's effective dependencies, then bring the volume back and verify that the service resumes only after the correct filesystem is present. They also confirm that no files were written to the root filesystem beneath the bare mountpoint. A second fault removes the remote storage after startup and checks whether the service detects failed I/O rather than serving stale success.",
        "findmnt -no SOURCE,FSTYPE,OPTIONS /srv/index\nsystemctl status srv-index.mount\nsystemctl show index-writer.service -p RequiresMountsFor",
        "Failing a service closed when its data mount is absent reduces apparent uptime, but protects the intended data path from split storage. Long mount timeouts can delay boot and incident response, while a short timeout can reject a recoverable transient. Measure cold-boot readiness, mount retry behavior, and root filesystem usage during the fault. If the storage is intentionally optional, make that a different application contract with a defined fallback; do not reuse an optional boot rule as an implicit guarantee of safe application operation.",
        ["Do not check only whether the mountpoint directory exists.", "Do not assume nofail means dependent services will fail safely.", "Do not ignore what is written beneath a mountpoint while the volume is absent."],
        ["devops/systemd-dependency-readiness-contract", "devops/persistent-storage", "devops/linux-service-diagnostics"],
    ),
    lesson(
        "linux-mdraid-degraded-rebuild",
        "Linux md RAID recovery: identify the failed member before rebuilding",
        "A degraded redundant array may still serve reads and writes while one more failure could remove that margin.",
        "Software RAID status identifies array level, active members, failed members, and rebuild progress. The member path alone is not enough to locate physical hardware or the provider attachment: map it through stable device IDs, serials, and array metadata before touching a disk. Adding a replacement to a degraded array can start reconstruction, which competes with application I/O and exposes unreadable blocks on surviving members. RAID is not a backup; deletion, corruption, and many operator mistakes propagate across members. Recovery therefore protects a recent independent backup, limits application load if needed, and checks both the array and data after rebuild.",
        "A four-member RAID10 array backing an image cache reports one failed member. The responder records md status, event count, member serials, and the last successful restore test, then confirms which physical or virtual attachment failed through an independent inventory. A disposable array exercise removes that member, observes service latency, and adds a known blank replacement only after matching its serial to the intended slot. During rebuild, the team tracks progress, read errors, and API tail latency. A second fault simulates a mistaken replacement selection; the runbook must stop before writing to a healthy member. Return to service requires a nondegraded array state and a sample of image hashes read through the application.",
        "cat /proc/mdstat\nmdadm --detail /dev/md0\nlsblk -o NAME,SERIAL,SIZE,TYPE",
        "Reconstruction consumes disk bandwidth and can lengthen client response times; an aggressive speed target may deepen latency, while a very slow target prolongs reduced redundancy. Monitor both rebuild state and user-path errors. A completed rebuild does not certify the newest application backup or catch corruption that predates the member loss. Keep evidence of the member identity, replacement mapping, and post-rebuild checks. If the array level has no redundancy, do not describe a failed member as a routine degraded rebuild: recovery may require restoring from backup.",
        ["Do not remove a member based only on a transient device letter.", "Do not treat RAID redundancy as an application backup.", "Do not declare recovery complete at 100% rebuild without data and service checks."],
        ["devops/backup-and-recovery", "devops/volume-snapshot-recovery", "devops/capacity-load-testing"],
    ),
    lesson(
        "linux-io-latency-attribution",
        "Linux I/O latency: distinguish device wait from an application queue",
        "A slow storage-backed request is an end-to-end delay, not a single disk utilization percentage.",
        "The request may wait in an application pool, filesystem, block queue, controller, network-attached volume, or database lock before a device reports completion. iostat extended fields describe observed device requests and queueing over a sampling interval; await includes time spent waiting for the requests represented there, and it is not the same as an application's full request latency. High utilization alone is ambiguous on concurrent storage devices. Compare read and write behavior, throughput, queue depth, device errors, and application tail latency during the same interval, then test a change one bottleneck at a time.",
        "A media transcoder's metadata writes slow from 18 ms to 430 ms at peak load. The operator samples iostat over successive intervals instead of trusting its first since-boot average, correlates the affected device with the actual metadata mount, and checks application queue wait separately. The volume shows rising write await and queue length, while reads remain steady. A test cohort reduces batch flush concurrency from 23 to 9, after which device queue depth and the 99th-percentile metadata write time fall together. If the application remains slow while device waits return to baseline, the investigation moves to locks or thread-pool saturation instead of purchasing larger disks without evidence.",
        "findmnt -no SOURCE /srv/media-meta\niostat -xz 2 4\njournalctl -k -n 60",
        "Longer sampling windows smooth spikes and may conceal a short stall; very short windows can produce noisy rates. Tracing every I/O on a busy host has CPU and log costs, so reserve it for a bounded investigation after inexpensive counters identify the device and interval. A smaller batch may reduce throughput even as tail latency improves; assess both against the service objective. For network-backed volumes, provider throttling and path failures can raise latency without high local device utilization. Preserve the before-and-after workload rate when judging an optimization.",
        ["Do not interpret the first iostat line as a fresh interval sample.", "Do not diagnose from utilization percentage without queue and latency data.", "Do not compare device and application latency from different time windows."],
        ["devops/capacity-load-testing", "devops/cpu-throttling-diagnosis", "devops/network-path-diagnosis-project"],
    ),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({item["path"]: item["title"] for item in specs})
titles[project_path] = "Linux storage fault drill: space, mount, repair, RAID, and latency"
titles[quiz_path] = "Linux storage decisions: failure and recovery quiz"
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
    ("Linux storage pressure and repair", "Attribute full disks, grow layered filesystems, and contain read-only failures.", related_paths[:3]),
    ("Linux storage continuity", "Verify mounts, rebuild degraded arrays, and isolate I/O latency.", related_paths[3:]),
]:
    by_path[course]["data"]["modules"].append({"title": heading, "summary": summary, "lessons": paths})
    by_path[course]["body"] += f"<h2>{html.escape(heading)}</h2><p>{html.escape(summary)}</p>" + links(paths)
by_path[course]["updated_at"] = stamp

for index, item in enumerate(specs):
    path = item["path"]
    row = copy.deepcopy(by_path["devops/continuous-integration"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
               title=item["title"], summary=item["summary"], subject="devops",
               category="DevOps", difficulty="Advanced", tags=["devops", "linux", "storage-operations"],
               sort_order=26510 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"kind": "tutorial", "reading_minutes": 7,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": course, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in [*item["related"], project_path, quiz_path]]}
    row["body"] = (
        f"<p>{html.escape(item['definition'])}</p><h2>Operational decision</h2>"
        f"<p>{html.escape(item['decision'])}</p>"
        f'<pre><code class="language-bash">{html.escape(item["sample"])}</code></pre>'
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
               summary="Exercise six Linux storage failure boundaries on disposable volumes and services.",
               difficulty="Advanced", sort_order=26590,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 13,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in related_paths]}
project["body"] = (
    "<p>Build a disposable Linux storage lab with a synthetic ledger service, a separate data mount, a four-member RAID10 array on virtual disks, and an independent backup. Keep a ledger of device identities, filesystem types, mount sources, application sequence IDs, and measured request latency. Save a pre-fault data copy. No repair, resize, or member replacement in this exercise should touch an irreplaceable volume.</p>"
    "<h2>Trace pressure and layered growth</h2><p>Fill the ledger mount with controlled test data, then unlink a large open log. Compare df, du, inode counts, and open-file evidence; free space must return only after the owner releases the descriptor through its supported path. Expand a clone through its actual provider, partition, encrypted mapping, logical volume, and filesystem layers as applicable. Record each layer's before-and-after size and prove a synthetic write at the mounted path.</p>"
    "<h2>Fail the mount and filesystem</h2><p>Boot a VM without its expected data volume. The management plane should remain reachable while the ledger writer stays stopped and no fallback files appear under the bare mountpoint. Inject a read-only mount or simulated device error on a clone. Preserve the first kernel and application errors, stop writes, and practice type-specific inspection or repair only after the filesystem is detached. Compare recovered ledger sequence IDs with the independent backup and application records before admitting a writer.</p>"
    "<pre><code class=\"language-text\">Acceptance ledger\nSpace: source and owner identified; write succeeds after controlled release\nGrowth: provider-to-filesystem layer sizes agree at the mounted path\nMissing mount: writer stopped; bare mountpoint remains empty\nRepair: detached clone checked; application sequence IDs reconciled\nRAID: replacement serial verified; array nondegraded; hashes match\nLatency: device and application intervals aligned; throughput recorded</code></pre>"
    "<h2>Recover redundancy and diagnose delay</h2><p>Remove one member from the disposable redundant array, map the failed slot by serial and metadata, then rebuild onto a known replacement. Track rebuild progress, unreadable blocks, and user-path latency. Refuse a deliberately mislabeled replacement before it is added. Finally, apply a controlled write load, compare per-interval device waits with application queue time, and change only one concurrency limit. The final evidence includes the array state, file hashes, request outcomes, and a repeatable rollback to the original load setting.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not repair a mounted production filesystem during the drill.</li><li>Do not identify a replacement disk by a changing device letter.</li><li>Do not declare a storage change complete without a real application write and read.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*related_paths, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Linux storage fault drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("What does df measure that du may miss?", ["Allocated space on the mounted filesystem, including open unlinked files", "Only directory names", "Only the user's home quota"], "The commands use different accounting views."),
    ("Why can deleting a large open log fail to free space?", ["Its process still holds the file descriptor", "The file has no inode", "df never updates"], "Blocks remain until the final open reference closes."),
    ("What must grow before the filesystem can use new provider space?", ["Every applicable block, partition, mapping, and volume layer beneath it", "Only the application cache", "Only the mountpoint directory"], "A filesystem cannot exceed the exposed backing block device."),
    ("What proves a filesystem expansion reached the service?", ["New capacity at the correct mount plus an application write and read", "A larger provider disk in the console", "A changed transient device letter"], "The service consumes the mounted filesystem."),
    ("What should happen first after unexpected read-only errors?", ["Contain writes and preserve kernel, device, and application evidence", "Force a read-write remount", "Erase the journal"], "The cause must be known before repair."),
    ("Where should modifying filesystem repair be rehearsed?", ["On a detached disposable clone with a recovery copy", "On the busy live mount", "On an unrelated empty directory"], "The repair boundary must protect live data."),
    ("Why is a mountpoint directory check insufficient?", ["The directory can exist on the root filesystem without the data volume", "Directories cannot be empty", "The mount source never changes"], "Check the mounted source and service requirement."),
    ("What can nofail allow during boot?", ["Boot can continue without that filesystem", "Every dependent service becomes safe automatically", "The missing data is reconstructed"], "Application behavior needs its own fail-closed rule."),
    ("How should a failed RAID member be identified?", ["Map array metadata to stable serial and physical or provider attachment", "Use only the current /dev letter", "Pick the hottest disk"], "A wrong selection can erase a healthy member."),
    ("Does a completed RAID rebuild replace a backup test?", ["No; data and application checks are still required", "Yes; reconstruction verifies all business records", "Only when latency is high"], "Redundancy does not guard against all loss modes."),
    ("What does iostat await omit from an API request?", ["Application queueing and other work outside the reported device requests", "All device waiting", "The sample interval"], "Device and end-to-end latency are different boundaries."),
    ("Why compare metrics from the same interval after a concurrency change?", ["To test whether device waits and user latency moved with the same workload", "To replace backups", "To make one utilization number equal a service objective"], "Unaligned samples can support a false diagnosis."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path],
            summary="Twelve decisions on disk pressure, growth, repair, mounts, RAID, and I/O latency.",
            sort_order=26600, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in related_paths],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Choose the evidence that separates free space, mount state, repair safety, redundancy, and request latency. A storage command succeeding is not enough to put a writer back in service.</p>"
    "<h2>Review these lessons</h2>" + links(related_paths)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-linux-host-change-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not diagnose a storage incident from a single utilization figure.</li><li>Do not mistake a mountpoint directory for its expected filesystem.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Linux storage decisions</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for source, targets in {
    "devops/inode-exhaustion-recovery": [related_paths[0]],
    "devops/ephemeral-storage-limit-accounting": [related_paths[0]],
    "devops/persistent-storage": [related_paths[1], related_paths[3]],
    "devops/volume-snapshot-recovery": [related_paths[1], related_paths[2], related_paths[4]],
    "devops/systemd-dependency-readiness-contract": [related_paths[3]],
    "devops/backup-and-recovery": [related_paths[2], related_paths[4], project_path],
    "devops/capacity-load-testing": [related_paths[5]],
    "devops/linux-service-diagnostics": [related_paths[2], related_paths[3]],
    "devops/luks-recovery-key-drill": [related_paths[1]],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Linux storage follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1,
                  "total_records": len(rows)}))
