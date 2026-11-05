"""Add original systemd service operations to DevOps fixtures."""

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
project_path = "devops/systemd-service-fault-drill-project"
quiz_path = "quizzes/devops-systemd-operating-decisions"


def lesson(slug, title, summary, definition, decision, sample, cost, mistakes, related):
    return dict(path="devops/" + slug, title=title, summary=summary,
                definition=definition, decision=decision, sample=sample,
                cost=cost, mistakes=mistakes, related=related)


specs = [
    lesson(
        "systemd-dependency-readiness-contract",
        "systemd dependencies: separate unit ordering from application readiness",
        "Starting after a database unit is not proof that the database accepts a transaction.",
        "A systemd unit can pull another unit into a start transaction and order itself relative to it, but those are different relationships. Wants and Requires express activation dependencies; After and Before express ordering. After alone does not start the named service, and a started dependency may still be unable to serve an application request. Type=simple can report a service start before its process has finished initializing. A daemon that supports Type=notify can report readiness after its own initialization; otherwise the application needs a specific health check before downstream traffic is admitted. A retrying client should also tolerate later dependency outages after boot.",
        "A settlement API needs a local certificate agent and a reachable database. It starts after the certificate unit, but does not assume that unit success guarantees a valid certificate. The API verifies its credential file, makes a bounded database connection attempt, and reports ready only after both checks pass. If the database is remote, the deployment avoids inventing a local systemd unit dependency for it. The operator tests boot with the certificate unit delayed, a database accepting TCP but rejecting authentication, and a database outage after startup. The service should either remain not ready or fail visibly; it must not enter the load balancer merely because systemctl reports active.",
        "[Unit]\nWants=certificate-agent.service\nAfter=certificate-agent.service\n[Service]\nType=notify\nExecStart=/opt/settlement/bin/settlement-api\nReadiness signal: sent only after credential and database checks",
        "Stronger dependency wiring can propagate failures or create ordering cycles; weak wiring may require application retries. Type=notify requires the process to implement the notification protocol, so changing only the unit file can leave startup waiting until timeout. Measure cold start, dependency recovery, and readiness transitions. A boot test must check a real user path, not merely a green unit status. Preserve a bounded startup timeout and a clear failure log so operators can distinguish unavailable dependencies from a deadlocked application.",
        ["Do not expect After to start its named unit.", "Do not treat active as proof of application readiness.", "Do not set Type=notify unless the process sends readiness notifications."],
        ["devops/linux-service-diagnostics", "devops/kubernetes-probes", "devops/load-balancer-health-semantics"],
    ),
    lesson(
        "systemd-restart-rate-budget",
        "systemd restarts: bound crash loops and preserve evidence before resetting failures",
        "Automatic restart is a recovery attempt, not a cure for a bad release or missing dependency.",
        "A systemd service can restart after selected exit failures. RestartSec delays the next attempt; StartLimitIntervalSec and StartLimitBurst constrain the number of starts in a window. When the limit is hit, later starts can be rejected until the condition is cleared or the interval passes. The correct values depend on how long the service needs to initialize and whether repeated starts damage a dependency. Restart=on-failure does not normally restart a service intentionally stopped by an operator. A crash-loop alarm should report the first meaningful failure and the current limit state rather than burying the cause under dozens of identical startup lines.",
        "A report renderer crashes immediately because a credential path is missing. Its unit permits four starts in twelve minutes with a 31-second restart delay. The fourth failure halts automated retries and pages the service owner. The operator captures the first exception, unit properties, credential mount state, and release ID. After restoring the credential, they test one explicit start and the report endpoint; only then do they reset the failed state if the start limit needs clearing. Increasing the burst count to 400 would spend CPU and flood logs without fixing the missing file. The same unit is tested for a recoverable single crash, a persistent configuration error, and a requested stop.",
        "[Unit]\nStartLimitIntervalSec=12min\nStartLimitBurst=4\n[Service]\nRestart=on-failure\nRestartSec=31s\nIncident evidence: first error, last exit, restart count, release ID",
        "A longer delay slows recovery from a transient crash; a shorter delay can amplify a dependency outage and consume host resources. Rate limits also affect manual starts, so the runbook must say when a reset is justified. Monitor exit cause and failed-unit state separately. A process that catches every fatal error and keeps running may never trigger restart logic, while a process that exits zero after a failed job may be classified as successful. Verify the application's exit status contract alongside systemd's restart configuration.",
        ["Do not increase the restart burst before diagnosing a deterministic failure.", "Do not reset failure state without retaining the first useful log and exit status.", "Do not assume an operator stop is equivalent to a process crash."],
        ["devops/linux-service-diagnostics", "devops/alert-design", "devops/credential-incident-rotation"],
    ),
    lesson(
        "systemd-credential-sandbox-boundary",
        "systemd service credentials: pass files through a narrow runtime boundary",
        "A service environment variable is easy to inherit and inspect; a credential file has a different exposure path.",
        "systemd can load a credential into a unit-specific, read-only directory and provide its location through CREDENTIALS_DIRECTORY. The daemon can read that file without placing the secret value directly in a unit Environment line or command argument. This does not protect a compromised process that is allowed to read the credential, and root or the service owner can still be within the trust boundary. Sandboxing options such as a read-only system tree and a managed state directory reduce incidental write access, but each option must be checked against the daemon's actual filesystem needs. Credential rotation usually requires a unit restart or explicit reload path that opens the new material.",
        "A webhook dispatcher uses a signing key stored in a protected host file. Its unit loads that file as a named credential, runs under a dedicated unprivileged identity, writes only to a managed state directory, and reads the key from the credential directory at startup. The operator verifies file ownership, the process's effective user, and the permissions of the material presented to the unit. They rotate the source key, restart or reload through the supported path, and verify a newly signed synthetic request while an old-key overlap window is still valid. A failed reload must leave an explicit alarm, not a silent mixture of signatures from old and new workers.",
        "[Service]\nUser=webhook-dispatch\nLoadCredential=signing-key:/etc/secure/webhook/signing-key\nProtectSystem=strict\nStateDirectory=webhook-dispatch\nExecStart=/opt/webhook/bin/dispatcher\nApplication reads: $CREDENTIALS_DIRECTORY/signing-key",
        "Credential loading adds a per-service file lifecycle and requires a tested renewal path. A strict filesystem sandbox may break runtime writes to unexpected directories, so inspect actual file access during a disposable rollout. Secret values should not enter process arguments, unit files, or logs. Rotate the underlying credential before it expires and measure from source update to every process using the new generation. A credential copied to an unprotected host path is still vulnerable even if the unit references it through LoadCredential.",
        ["Do not put a signing key value in Environment or ExecStart.", "Do not assume a running service reloads a changed credential automatically.", "Do not enable a strict sandbox without testing required write paths."],
        ["devops/secret-rotation-rollout", "devops/service-account-token-boundaries", "devops/config-secret-generation-consistency"],
    ),
    lesson(
        "systemd-journal-retention-evidence",
        "systemd journals: retain failure evidence without exhausting the host disk",
        "A useful journal policy needs both a storage mode and a space budget.",
        "systemd-journald can keep records in volatile storage or on a persistent filesystem, depending on configuration and directory state. A service's stdout and stderr can enter the journal, but an application that logs a credential or personal payload leaks it there too. Size limits bound stored journal files, yet active files and disk pressure from other writers can make real usage differ from a simple configured number. A node restart may erase volatile logs that would explain the outage. A production incident workflow therefore checks storage mode, the available retention horizon, forwarding health, and the exact service and boot identifiers needed to query an earlier failure.",
        "A payment proxy enters a crash loop overnight. The operator needs the first error from the previous boot, not just the latest restart. On a disposable host, they set persistent journaling with a 768 MiB system budget, generate controlled log volume, reboot, and query records by unit and previous boot. They confirm the first failure remains available long enough for incident response and that log forwarding receives the same event ID. They then simulate a disk filling from another process and verify whether journal retention behaves as expected. Sensitive request bodies are redacted at the application boundary; shrinking journal retention is not a data-protection substitute.",
        "[Journal]\nStorage=persistent\nSystemMaxUse=768M\nReview: previous-boot records for payment-proxy.service\nForwarding: alert if delivery stalls\nLog contract: event ID present, credential and payload absent",
        "More local history consumes disk and write bandwidth; less history weakens incident reconstruction when central forwarding fails. Active journal files may not be removed immediately to meet a vacuum target. Rate limits can also suppress repetitive events, making an absence of logs ambiguous during a storm. Monitor journal disk use, forwarding lag, and dropped-message indicators. Set the budget against the same filesystem's application data and recovery reserve. A unit that emits large stack traces on every 31-second restart can exhaust a small budget before anyone arrives to investigate.",
        ["Do not assume previous-boot logs exist with volatile storage.", "Do not place secrets or full sensitive payloads in journal-bound output.", "Do not interpret a size limit as an exact immediate disk-usage ceiling."],
        ["devops/log-pipeline-retention", "devops/incident-response", "devops/file-descriptor-exhaustion"],
    ),
    lesson(
        "systemd-timer-catchup-idempotency",
        "systemd timers: treat missed-run catch-up as a trigger, not a work ledger",
        "Persistent calendar timers may trigger after downtime, but they do not replay every missed business interval.",
        "A systemd timer activates a service on a configured schedule. For a calendar timer, Persistent=true can cause a catch-up activation after the timer was inactive when it should have fired. That does not mean every missed period is replayed as a separate job. If the paired service is still active at a scheduled time, starting the same unit again does not create a parallel copy by default. These properties prevent some overlap but do not guarantee that every business partition was processed. The job must keep a durable cursor or interval ledger, use a unique work identity, and expose the oldest unprocessed period.",
        "A reconciliation job is scheduled every hour. Its host is down for seven hours, then boots at 14:00. The timer may trigger a catch-up start, but the service reads its database ledger and processes each of the seven missing hourly windows in order, with a checkpoint after each one. If an earlier run is still active, the next timer activation is not treated as a second worker; the service's own cursor continues the backlog. A deliberately failed window remains visible for retry. The operator tests host downtime, a job running past the next tick, and a crash after the external effect but before checkpoint. Unique window IDs prevent duplicate settlement during recovery.",
        "Timer: hourly calendar activation, Persistent=true\nHost gap: 7 missed hours\nRequired work: 7 ledger windows, not 1 assumed timer event\nCheckpoint: after verified effect per window\nDuplicate guard: settlement-window ID\nAlert: oldest unprocessed window age",
        "A tight schedule may make a long job appear permanently behind; adding more timer firings will not add safe parallelism for one active unit. A database-backed interval ledger costs writes and indexes but supplies the recovery evidence that a timer cannot. Persistent catch-up also can create a startup load spike after maintenance, so bound the number of windows processed per run and preserve a next-run signal. Test timezone and daylight-saving behavior for calendar expressions. A timer's next elapse timestamp is scheduling data, not proof that past business work completed.",
        ["Do not infer seven completed jobs from seven missed timer periods.", "Do not rely on timer behavior as the sole duplicate-effect guard.", "Do not use a green timer status as proof the application cursor advanced."],
        ["devops/cronjob-schedule-safety", "devops/scheduled-function-overlap-control", "devops/runbook-automation-guardrails"],
    ),
    lesson(
        "systemd-socket-activation-boundary",
        "systemd socket activation: preserve the listener without hiding service failure",
        "A socket unit can hold a listening endpoint while the service process starts or restarts.",
        "With systemd socket activation, the service manager opens a listening socket and passes its file descriptor to a compatible daemon. A socket unit with Accept=no normally activates one matching service that handles all accepted traffic; the daemon must use the inherited descriptor rather than trying to bind the same address again. A healthy socket unit does not prove the application is healthy: requests can queue or fail while the service crashes, starts slowly, or rejects work. Socket activation is an endpoint-ownership mechanism, not an application readiness check or a substitute for a load balancer's user-path probe.",
        "A local image processor listens on a Unix socket. The operator enables its socket unit, leaves the service stopped, and sends one synthetic request. The service starts, accepts the inherited descriptor, and records the request ID. Then they kill the service during a burst of 47 requests and observe connection outcomes, queueing, restart delay, and whether any request effect ran twice. The service must not unlink a socket path it did not create. If the app cannot consume passed descriptors, the team keeps ordinary service-owned binding instead of turning on a socket unit that merely holds a port and masks the incompatibility.",
        "Socket: image-worker.socket\nAccept=no: one image-worker.service handles connections\nFirst request: activates service through inherited descriptor\nFault: kill service during 47 synthetic requests\nVerify: connection outcomes, effect IDs, restart time, user-path probe",
        "Keeping a listener open across service restarts can reduce bind races, but it can also let the socket backlog grow while no worker can answer. Backlog capacity and client timeouts therefore need measurement under a crash, not only during clean startup. An idle socket may show active even when its service is rate-limited and unavailable. Observe both units plus a real request, and alert on a service that repeatedly fails after activation. A long-running effect still needs an idempotency key because a client may retry after losing the response.",
        ["Do not enable a socket unit for a daemon that cannot use inherited descriptors.", "Do not treat an active socket as application readiness.", "Do not remove a socket path owned by the service manager from the daemon."],
        ["devops/connection-drain-boundary", "devops/retry-timeout-budgets", "devops/linux-service-diagnostics"],
    ),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({item["path"]: item["title"] for item in specs})
titles[project_path] = "systemd service fault drill: readiness, restart, timer, and socket recovery"
titles[quiz_path] = "systemd operating decisions: service lifecycle and recovery quiz"
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
    ("systemd service lifecycle", "Test startup dependencies, crash-loop limits, and credential access.", related_paths[:3]),
    ("systemd evidence and triggers", "Retain logs, recover missed schedule work, and verify socket activation.", related_paths[3:]),
]:
    by_path[course]["data"]["modules"].append({"title": heading, "summary": summary, "lessons": paths})
    by_path[course]["body"] += f"<h2>{html.escape(heading)}</h2><p>{html.escape(summary)}</p>" + links(paths)
by_path[course]["updated_at"] = stamp

for index, item in enumerate(specs):
    path = item["path"]
    row = copy.deepcopy(by_path["devops/continuous-integration"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
               title=item["title"], summary=item["summary"], subject="devops",
               category="DevOps", difficulty="Advanced", tags=["devops", "systemd", "linux-services"],
               sort_order=26110 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"kind": "tutorial", "reading_minutes": 7,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": course, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in [*item["related"], project_path, quiz_path]]}
    row["body"] = (
        f"<p>{html.escape(item['definition'])}</p><h2>Operational decision</h2>"
        f"<p>{html.escape(item['decision'])}</p>"
        f'<pre><code class="language-text">{html.escape(item["sample"])}</code></pre>'
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
               summary="Fault-test a disposable Linux service with dependency delays, restart limits, credentials, journal retention, timer catch-up, and socket activation.",
               difficulty="Advanced", sort_order=26190,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 12,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in related_paths]}
project["body"] = (
    "<p>Use a disposable Linux VM with systemd and a synthetic service called settlement-api. Version-control its service, timer, and socket unit definitions. Before applying them, verify unit syntax with the installed systemd tooling and inspect the effective settings. Keep one ledger of synthetic request IDs and completed effects outside the service process. The exercise tests lifecycle behavior; do not reuse a production credential or endpoint.</p>"
    "<h2>Inject startup and restart faults</h2><p>Delay the local certificate agent and present a database endpoint that accepts TCP but rejects authentication. Confirm the service does not report ready prematurely. Crash it once and measure recovery, then make it fail deterministically until the start limit is reached. Preserve the first error and exit status before resetting failure state. Rotate a credential file and show that every process uses the intended generation after the supported restart or reload path. Verify the process cannot write outside its managed state directory while it still performs its legitimate work.</p>"
    "<pre><code class=\"language-text\">Synthetic acceptance\nReadiness: withheld until credential and database checks pass\nCrash loop: 4 starts within 12 minutes, then visible failed state\nCredential: old and new generation recorded per process\nJournal: first failure available after reboot within disk budget\nTimer: 7 missed hourly windows processed from ledger\nSocket: 47-request burst reconciled by request ID</code></pre>"
    "<h2>Preserve evidence and scheduled work</h2><p>Generate a controlled log burst, reboot, and query the previous boot's first settlement error by unit. Confirm the journal budget and central-forwarding behavior. Pause the host for seven hourly timer periods; when it returns, the job must process seven ledger windows even if the timer issues only a catch-up start. Crash after one window's effect but before its checkpoint and verify that the unique window ID prevents a second settlement.</p>"
    "<h2>Exercise the listener boundary</h2><p>Run a separate socket-compatible worker. Start only its socket unit, send an initial request, then kill the service during 47 synthetic requests. Record accepted, timed-out, and retried connections, plus completed effect IDs. A socket reporting active while the service cannot handle a user path fails the check. Keep the final evidence as unit versions, commands, first-error logs, request ledger, and measured recovery intervals.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not infer readiness from unit activation alone.</li><li>Do not let a timer substitute for the durable work ledger.</li><li>Do not treat a listening socket as proof that a service can answer.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*related_paths, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>systemd service fault drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("Does After= start its named unit?", ["No; it only orders units that are started", "Yes; it always starts the dependency", "Only after a reboot"], "Ordering and activation are separate relationships."),
    ("What does Type=notify require from a daemon?", ["A readiness notification after initialization", "Only a listening TCP socket", "A journal entry"], "The unit cannot fabricate application readiness."),
    ("Why limit automatic restarts?", ["To stop a deterministic crash loop from consuming resources and hiding the first cause", "To prevent every transient restart", "To delete stale journals"], "Bound recovery attempts and preserve evidence."),
    ("What should happen before reset-failed during an incident?", ["Capture first error, exit status, and current limit state", "Increase burst count without inspection", "Delete the unit file"], "Resetting state must not erase the diagnosis."),
    ("Where can LoadCredential expose its named file to the process?", ["The unit's credential directory", "Only in ExecStart arguments", "Only through journal output"], "The application reads the loaded credential file through its runtime path."),
    ("Does changing a credential source file automatically update every running process?", ["No; use the supported reload or restart path and verify generation", "Yes, every process rereads it immediately", "Only if the journal is persistent"], "Rotation requires an application lifecycle check."),
    ("Why inspect Storage= before relying on previous-boot logs?", ["Volatile journal data may disappear on reboot", "It changes the service's network port", "It proves every log was forwarded"], "Retention mode determines local history."),
    ("Can a journal size limit act as an exact immediate ceiling?", ["No; active files and other disk users affect observed space", "Yes, every active file is removed instantly", "Only for service stdout"], "Budget and real disk use require separate monitoring."),
    ("A host misses seven hourly timer periods. What should process seven business windows?", ["A durable application interval ledger", "Seven assumed timer catch-up executions", "The journal vacuum"], "A persistent timer trigger is not a replay ledger."),
    ("What happens when the same service unit is already active at a timer tick?", ["It is not launched as a second independent copy by that activation", "A second copy always starts", "The unit file is deleted"], "The job still needs a cursor for unfinished work."),
    ("What must a socket-activated daemon support?", ["Accepting the inherited listening descriptor", "Binding the same address again", "Deleting the manager-owned socket path"], "Socket activation passes ownership of the listener."),
    ("What proves a socket-activated service is useful during a crash?", ["A real request and effect check alongside both unit states", "An active socket unit alone", "A successful daemon-reload alone"], "A listener can remain active while the worker cannot answer."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on systemd dependencies, restart limits, credentials, journals, timers, and socket activation.",
            sort_order=26200, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in related_paths],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Choose the evidence that proves a host service is ready, recoverable, and able to process scheduled or socket-triggered work. Unit activation is only one part of the application contract.</p>"
    "<h2>Review these lessons</h2>" + links(related_paths)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-redis-operating-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not mistake ordering for dependency activation.</li><li>Do not mistake a timer trigger or listening socket for completed business work.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>systemd operating decisions</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for source, targets in {
    "devops/linux-service-diagnostics": [related_paths[0], related_paths[1]],
    "devops/secret-rotation-rollout": [related_paths[2]],
    "devops/log-pipeline-retention": [related_paths[3]],
    "devops/cronjob-schedule-safety": [related_paths[4]],
    "devops/connection-drain-boundary": [related_paths[5]],
    "devops/load-balancer-health-semantics": [related_paths[0], related_paths[5]],
    "devops/scheduled-function-overlap-control": [related_paths[4], project_path],
}.items():
    row = by_path[source]
    row["body"] += "<h2>systemd operating follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1,
                  "total_records": len(rows)}))
