"""Add original delivery-measurement operating lessons to DevOps fixtures."""

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


def lesson(slug, title, summary, definition, decision, language, sample, cost, mistakes, related):
    return dict(path="devops/" + slug, title=title, summary=summary,
                definition=definition, decision=decision, language=language,
                sample=sample, cost=cost, mistakes=mistakes, related=related)


specs = [
    lesson(
        "production-deployment-event-ledger",
        "Deployment frequency: count activated production changes from an event ledger",
        "Pipeline runs, preview builds, and production activations are different events.",
        "A deployment-frequency measure needs a durable record of when a service change became active in production. A CI job can pass without publishing anything; a preview can deploy without serving users; and a failed production attempt may leave the old version active. Define the service boundary and count successful activations inside a fixed reporting window. Keep deployment identity, source revision, artifact digest, target environment, activation time, and result in one ledger. If a rollback activates an earlier artifact, record that as a distinct production action under the stated counting policy. Do not silently change the policy when delivery architecture moves from server releases to edge or flag-based promotion.",
        "A claims portal runs 43 pipeline jobs during September. Twenty-nine attempts target production, but only 26 new states become active. Three attempts fail before traffic moves. The frequency numerator is 26 under this portal's definition; the failed attempts remain in the operational ledger for reliability analysis. A content-only release counts if it changes the production site under the same service boundary. The team records the activation timestamp from hosting control-plane evidence, not the commit time or the command invocation. It reviews the first and last day of the month in one timezone and confirms that a retry with the same deployment ID did not create a second event.",
        "sql",
        "SELECT COUNT(DISTINCT deployment_id) AS active_production_deployments\nFROM deployment_events\nWHERE service_id = 'claims-portal'\n  AND environment = 'production'\n  AND result = 'active'\n  AND activated_at >= '2026-09-01T00:00:00Z'\n  AND activated_at < '2026-10-01T00:00:00Z';",
        "With an index on service, environment, and activation time, a window query scans the matching events rather than the full ledger; DISTINCT adds work when duplicate IDs remain. A unique deployment ID at ingestion is preferable. Reporting one monthly count hides long pauses and release bursts, so inspect the timeline as well. Count user-serving activations consistently and publish the exclusions. The number should not rise merely because a pipeline retried, a preview was created, or a failed attempt produced another log row.",
        ["Do not count every CI run as a production deployment.", "Do not omit failed attempts from the evidence ledger even when the frequency numerator excludes them.", "Do not compare services with different production and activation definitions as if they share one measure."],
        ["devops/release-evidence-record", "devops/build-deployment-live-route-evidence", "devops/ci-deployment-concurrency"],
    ),
    lesson(
        "commit-to-live-change-lead-time",
        "Change lead time: join committed work to its first live artifact",
        "A merge timestamp alone cannot tell when a specific commit first served users.",
        "Change lead time connects a source change to the first successful production deployment that contains it. A reliable calculation needs artifact lineage: commits included in the built artifact, the artifact digest promoted, and the production activation time. Rebuilding the same commit may create another artifact; redeploying an old artifact should not create a new first-live time for its commits. Commit timestamps can be backdated or affected by clock error, so record the version-control event and any timestamp correction policy. For a large batch, each included change has its own elapsed time even though all share one activation. Report a distribution rather than reducing every change to the last commit in the batch.",
        "Three changes enter the mainline at 09:00, 11:30, and 15:00 UTC. The tested artifact containing all three first becomes active at 17:00. Their lead times are 8 hours, 5 hours 30 minutes, and 2 hours. The median is 5 hours 30 minutes; quoting only the 2-hour figure would hide the oldest change. If a later rollback reactivates an earlier artifact, it does not rewrite the first-live timestamp of those original commits. A correction deployed the next day is a new change with its own clock. Join the release receipt to the artifact manifest before calculating, and flag a missing commit-to-artifact edge instead of guessing.",
        "text",
        "Artifact A84 first live: 17:00 UTC\nCommit 91a entered: 09:00; lead time: 8 h\nCommit 72b entered: 11:30; lead time: 5 h 30 min\nCommit 47c entered: 15:00; lead time: 2 h\nMedian of three changes: 5 h 30 min\nMissing lineage: exclude with an explicit data-quality count",
        "Joining C commits to D deployment manifests can be expensive if every report recomputes artifact ancestry; persist a deduplicated commit-to-artifact relation and index it by commit and deployment. Measure ingestion gaps and impossible negative durations. Median and tail values explain the workflow better than an average alone, because one old change can dominate a batch. Keep queue, review, build, and waiting time as diagnostic sub-intervals, while the headline clock remains commit to first live activation.",
        ["Do not use merge time as a substitute for first production activation.", "Do not assign a whole batch the lead time of its newest commit.", "Do not silently turn a missing lineage edge into a zero-duration change."],
        ["devops/production-deployment-event-ledger", "devops/tested-artifact-digest-binding", "devops/merge-queue-candidate-verification"],
    ),
    lesson(
        "change-failure-intervention-attribution",
        "Change fail rate: attribute immediate intervention to a production deployment",
        "A failed change needs an incident link, not a guess from a red pipeline badge.",
        "A change-failure numerator counts production deployments that cause a problem requiring immediate intervention, under a documented attribution window and service boundary. A build that fails before release is a pipeline failure, not a production change failure. A rollback, urgent hotfix, or manual mitigation can establish intervention, but the team still needs evidence that a specific deployment caused the impairment. One incident can involve several deployments; count each implicated deployment once rather than counting alert notifications. Attribution can be uncertain when a dependency fails at the same time. Keep an unknown state until review rather than forcing every incident into a neat numerator.",
        "During a month, the portal has 26 successful production activations. Three distinct activations require urgent intervention after user-path checks fail. The observed change fail rate is 3 divided by 26, or about 11.5 percent. Two alerts for the same failed activation do not make it two failures. A database outage that begins before a deploy is investigated separately and is not automatically assigned to the newest version. The release ledger stores incident ID, first user impact, intervention type, evidence, attribution confidence, and review owner. Recalculate a past period when a review changes attribution, but keep a visible revision of the report.",
        "text",
        "Reporting period: 26 active production deployments\nAttributable failures: 3 distinct deployment IDs\nChange fail rate: 3 / 26 = 11.5% after rounding\nDuplicate alerts: deduplicated by deployment and incident\nUncertain cause: reviewed separately, not guessed\nInterventions: rollback, hotfix, or urgent mitigation",
        "A join between D deployments and I incident links is manageable with indexed IDs, but human attribution is the costly part. Keep the counting rule short enough for an operator to apply during an incident. A low rate can be misleading if teams stop recording hotfixes or use a long detection delay that pushes failures outside the chosen window. Read the rate with deployment volume, user impact, and SLO results; a team can achieve zero failures by shipping nothing.",
        ["Do not count pre-production build failures in the production change-failure numerator.", "Do not multiply one incident by its alert count.", "Do not equate the newest deployment with the cause before checking evidence."],
        ["devops/production-deployment-event-ledger", "devops/incident-response", "devops/canary-cohort-analysis"],
    ),
    lesson(
        "failed-deployment-recovery-clock",
        "Failed deployment recovery time: keep impact, detection, and restoration clocks distinct",
        "A recovered dashboard does not prove the user path recovered at the same moment.",
        "Recovery time for a deployment-caused failure needs an explicit impairment start and a verified restoration endpoint. Deployment activation, first user impact, alert detection, operator acknowledgement, rollback command, and successful public probe are separate timestamps. Choose and publish the clock used in the report; retain the other timestamps to explain detection and mitigation delay. Exclude unrelated infrastructure incidents from this change-specific measure while still tracking them in the broader incident program. If impact start is uncertain, record a bounded interval and label the measurement uncertain. A code rollback can finish before data repair or cache expiry restores the actual journey.",
        "A faulty release activates at 14:02. The first failed checkout occurs at 14:06, the alert fires at 14:14, the team starts rollback at 14:21, and a synthetic checkout plus real request sample pass at 14:55. Under a first-impact-to-verified-restoration rule, recovery takes 49 minutes. Detection lag is 8 minutes and the post-detection recovery interval is 41 minutes. A dashboard that turns green at 14:34 is not the endpoint if payment confirmation remains broken. Preserve the release ID, affected cohort, probe evidence, and timestamp sources so the incident review can reconstruct the interval.",
        "text",
        "Activation: 14:02\nFirst verified user impact: 14:06\nDetection: 14:14\nRollback started: 14:21\nUser path restored: 14:55\nFailed-deployment recovery time: 49 min\nDetection lag: 8 min; post-detection repair: 41 min",
        "Computing a duration per incident is O(1) after its evidence is assembled, but collecting trustworthy start and end times can require traces, synthetic checks, and customer reports. Report the distribution across incidents, including long tails and uncertain records. Avoid an average when a few severe events dominate user harm. A fast rollback should not appear as fast recovery if the old version cannot read candidate-written data or a stale edge cache still serves the bad page.",
        ["Do not start every recovery clock at alert detection without saying so.", "Do not stop the clock when an operator presses rollback.", "Do not mix deployment-caused failures with unrelated outages in this measure."],
        ["devops/change-failure-intervention-attribution", "devops/synthetic-transaction-monitoring", "devops/serverless-version-data-rollback"],
    ),
    lesson(
        "deployment-rework-intent-ledger",
        "Deployment rework: identify unplanned repair releases without hiding planned work",
        "A hotfix can restore service while still consuming delivery capacity that the planned roadmap never budgeted.",
        "Deployment rework measures the share of production deployments made as unplanned work in response to a production incident. It differs from change fail rate: a failed deployment belongs to the failure numerator, while one incident may drive several subsequent repair deployments. Record the intent when a deployment is requested, link it to the incident, and preserve later corrections as auditable changes. If one deployment mixes a planned feature and an urgent fix, define an explicit classification rule and report the mixed case separately where volume matters. A silent relabel after the fact makes the trend impossible to trust.",
        "In the same 26-activation month, four activations are urgent repairs tied to production incidents. The observed rework share is 4 divided by 26, or about 15.4 percent. One incident caused two repair deployments because the first patch only fixed the API and the second corrected cached HTML. Both deployments consume delivery effort; the incident itself is counted once in the incident ledger. A planned security patch that follows the normal review and schedule is not automatically rework merely because it changes a vulnerability. For every release, keep request time, planned or repair intent, incident link if any, approving owner, and the public outcome.",
        "text",
        "Production activations: 26\nUnplanned incident-repair activations: 4\nRework share: 4 / 26 = 15.4% after rounding\nIncident with two repairs: two deployment events, one incident\nMixed feature and repair: separately flagged by policy\nAudit: preserve original intent and later correction",
        "Classification is O(D) review work for D deployments unless it is captured in the release workflow. Automated incident links reduce clerical cost but still need human review for mixed intent. A falling rework share can mean fewer incidents, more planned deployments in the denominator, or missed tagging; inspect the absolute repair count and customer impact alongside the ratio. Do not reward teams for suppressing incident links. Use the measure to find recurring repair paths and remove their causes.",
        ["Do not treat every unplanned deployment as an incident repair without an incident link.", "Do not count one incident as only one repair deployment when it required several.", "Do not hide mixed intent by changing labels after the report closes."],
        ["devops/production-deployment-event-ledger", "devops/incident-review-actions", "devops/failed-deployment-recovery-clock"],
    ),
]

project_path = "devops/delivery-measurement-ledger-project"
quiz_path = "quizzes/devops-delivery-measurement-decisions"
titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
titles[project_path] = "Project: build an auditable delivery and recovery measurement ledger"
titles[quiz_path] = "DevOps delivery measurement decisions"
assert all(item["path"] not in by_path for item in specs)
assert project_path not in by_path and quiz_path not in by_path
assert all(target in titles for item in specs for target in item["related"])


def links(paths):
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in dict.fromkeys(paths)
    ) + "</ul>"


for heading, summary, paths in [
    ("Delivery throughput evidence", "Count active production changes and trace committed work to its first live artifact.", [specs[i]["path"] for i in (0, 1)]),
    ("Failure and recovery evidence", "Attribute interventions, measure restored user paths, and classify repair releases.", [specs[i]["path"] for i in (2, 3, 4)]),
]:
    by_path[course]["data"]["modules"].append({"title": heading, "summary": summary, "lessons": paths})
    by_path[course]["body"] += f"<h2>{html.escape(heading)}</h2><p>{html.escape(summary)}</p>" + links(paths)
by_path[course]["updated_at"] = stamp

for index, item in enumerate(specs):
    path = item["path"]
    row = copy.deepcopy(by_path["devops/continuous-integration"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
               title=item["title"], summary=item["summary"], subject="devops",
               category="DevOps", difficulty="Advanced", tags=["devops", "delivery-measurement"],
               sort_order=25310 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"kind": "tutorial", "reading_minutes": 6,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": course, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in item["related"]]}
    row["body"] = (
        f"<p>{html.escape(item['definition'])}</p><h2>Operational decision</h2>"
        f"<p>{html.escape(item['decision'])}</p>"
        f'<pre><code class="language-{item["language"]}">{html.escape(item["sample"])}</code></pre>'
        f"<h2>Cost and verification</h2><p>{html.escape(item['cost'])}</p>"
        + "<h3>Common Mistakes</h3><ul>"
        + "".join(f"<li>{html.escape(mistake)}</li>" for mistake in item["mistakes"])
        + "</ul><h2>Connected lessons</h2>" + links([course, *item["related"]])
        + "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    )
    row["data"]["related"].extend({"path": target, "title": titles[target]} for target in (project_path, quiz_path))
    rows.append(row)

related_paths = [item["path"] for item in specs]
project = copy.deepcopy(by_path["devops/practice-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)),
               path=project_path, title=titles[project_path],
               summary="Reconstruct production delivery measures from immutable releases, artifact lineage, and incident evidence.",
               difficulty="Advanced", sort_order=25390,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 10,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in related_paths]}
project["body"] = (
    "<p>Build a disposable event ledger for one service. Seed 43 pipeline runs, 29 production attempts, and 26 distinct activations across a month. Attach artifact digests and commit sets to each activation, then create three deployment-caused incidents and four unplanned repair activations. The exercise passes only when repeated events, previews, failed pre-activation attempts, and unrelated outages are classified without inflating the headline measures. Use synthetic event IDs and avoid importing employee-performance data.</p>"
    "<h2>Define the event contract</h2><p>Store immutable deployment ID, service, environment, source revision, artifact digest, attempt result, activation time, and release intent. Keep commit-to-artifact membership in a separate relation. Link incidents to deployment IDs with impact start, detection, intervention, verified restoration, and attribution confidence. Require a reason for unknown or corrected classifications. Run a monthly report with a half-open UTC interval so midnight events cannot fall in two months. Review the first and last day manually against source receipts.</p>"
    "<pre><code class=\"language-text\">Synthetic acceptance\nProduction activations: 26, not 43 pipeline runs\nPre-activation failures: 3, retained outside frequency numerator\nAttributable failed activations: 3 / 26 = 11.5%\nUnplanned repair activations: 4 / 26 = 15.4%\nFirst impact 14:06 to verified recovery 14:55 = 49 min\nUnknown attribution: visible queue for review</code></pre>"
    "<h2>Inject ledger faults</h2><p>Replay one deployment event with the same ID and confirm the count remains 26. Promote an earlier artifact after rollback and prove that its original commits retain their first-live timestamps. Add two alerts for one failed activation and keep the change-failure numerator at one for that activation. Move a failed attempt to the end of the month; it must not become a successful activation merely because the pipeline ended. Make one incident cause two repair deployments and confirm both count as rework while the incident remains one record.</p>"
    "<h2>Review the measures together</h2><p>Show deployment timeline, change lead-time distribution, change fail rate, failed-deployment recovery durations, rework share, and missing-link counts. Compare the same service across periods without changing definitions. A shorter lead time is not a victory if user impact grows; a zero failure rate is not a victory if no changes reach production. Preserve report revisions so a later incident review can correct attribution without erasing the first published result.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not equate pipeline runs with live deployments.</li><li>Do not infer causation solely from event timing.</li><li>Do not stop recovery time at the rollback command.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*related_paths, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Delivery measurement ledger drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("Which event belongs in a production deployment count?", ["A distinct service change activated for production users", "A preview build", "A CI retry that never moved traffic"], "Count the user-serving activation under a fixed service boundary."),
    ("Why retain a failed pre-activation attempt?", ["For operational evidence even though it is not an active deployment", "To inflate frequency", "To give every commit zero lead time"], "Exclusion from one numerator does not erase the attempt."),
    ("What links a commit to its first live time?", ["Artifact membership plus successful production activation", "Only the merge request title", "The most recent pipeline run"], "Lineage connects source work to the artifact users received."),
    ("Three commits ship in one artifact. How many lead times exist?", ["Three, one per included change", "One, for the newest commit", "None until the next release"], "Each change has its own starting time."),
    ("A build fails before traffic moves. Is it a production change failure?", ["No; it failed before production activation", "Yes, every red build is one", "Only if it retried twice"], "The change-failure boundary is production impact."),
    ("Two alerts describe one failed deployment. How is the numerator counted?", ["One implicated deployment", "Two alerts", "Zero until a monthly report"], "Alert count is not deployment count."),
    ("What ends a failed-deployment recovery clock?", ["Verified restoration of the affected user path", "The rollback command", "The first green CPU chart"], "Recovery is observed at the user path."),
    ("Why record detection time separately from impact time?", ["To expose detection lag without hiding total user impairment", "To remove the impact interval", "To make every incident start at deploy time"], "The two clocks answer different questions."),
    ("One incident needs two urgent repair deployments. How many rework deployments?", ["Two", "One", "Zero because the incident is one"], "The rework numerator counts deployments."),
    ("A planned patch follows normal review. Is it automatically rework?", ["No; classify it by incident-driven unplanned intent", "Yes, every patch is rework", "Yes, if it lands on Friday"], "Patch type alone does not establish incident repair intent."),
    ("A deployment has uncertain incident attribution. What should the ledger show?", ["An explicit unknown state and review owner", "An invented causal link", "A deleted incident"], "Uncertainty is data that needs review."),
    ("Why read the five measures together?", ["A single ratio can improve while user impact or hidden repair work grows", "One number contains every user outcome", "Deployment frequency makes incident data unnecessary"], "Throughput and instability need shared context."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on deployment, lead-time, failure, recovery, and rework measurement.",
            sort_order=25400, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in related_paths],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Choose the event or time boundary that preserves the actual production outcome. A dashboard number is only useful when its numerator and exclusions can be reconstructed.</p>"
    "<h2>Review these lessons</h2>" + links(related_paths)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-browser-edge-security-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not count previews as production activations.</li><li>Do not stop a recovery clock before the user path is restored.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Delivery measurement decisions</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for source, targets in {
    "devops/release-evidence-record": [specs[0]["path"]],
    "devops/tested-artifact-digest-binding": [specs[1]["path"]],
    "devops/incident-response": [specs[2]["path"]],
    "devops/synthetic-transaction-monitoring": [specs[3]["path"]],
    "devops/incident-review-actions": [specs[4]["path"]],
    "devops/platform-product-slo-and-adoption": [project_path],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Delivery measurement follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1,
                  "total_records": len(rows)}))
