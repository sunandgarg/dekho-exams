"""Add original web-publishing operating lessons to the local DevOps fixtures."""

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
        "build-deployment-live-route-evidence",
        "Web publishing evidence: prove the build, deployment, and live route separately",
        "A successful local build and a pushed commit do not establish which page a public visitor receives.",
        "A content release crosses several boundaries: source revision, build artifact, hosting deployment, route resolution, and the response observed by a visitor. Each boundary can succeed while the next one fails. A build may write the wrong output directory; a hosting project may track another branch; a new deployment may be a preview; and a public route may still serve an older artifact. Record an immutable deployment identifier and the expected content revision before making a release claim. Then probe the public route through the same hostname and cache path used by readers. The response needs a status, a recognizable page marker, and a timestamp or revision that can be compared with the release record.",
        "For a training portal, revision 72 adds a guide under /devops/build-deployment-live-route-evidence. The release operator first records the commit and build artifact digest, then confirms that the production deployment names that commit and contains the generated route. A synthetic request fetches the public path, checks a successful status and the expected heading, and records the response's deployment marker. It repeats the request from a second network after cache expiry. If the route returns an old page, the operator does not close the change merely because the build command exited zero. The fault is isolated by comparing the artifact, deployment identifier, route configuration, and cache response in that order.",
        "bash",
        "set -euo pipefail\n: \"${SITE_ORIGIN:?set the public origin}\"\n: \"${EXPECTED_MARKER:?set the release marker}\"\npage=$(mktemp)\ntrap 'rm -f \"$page\"' EXIT\nstatus=$(curl --silent --show-error --location --output \"$page\" --write-out '%{http_code}' \"${SITE_ORIGIN}/devops/build-deployment-live-route-evidence\")\ntest \"$status\" = 200\ngrep -Fq \"$EXPECTED_MARKER\" \"$page\"",
        "The probe transfers O(B) bytes for a B-byte page and scans O(B) bytes for the marker. Running it once per deployed route can become expensive for a large catalog, so gate every changed route and sample unchanged routes by risk. A single successful response proves one observation, not global propagation. Store the observed status, resolved deployment ID, cache status, and content revision; repeat after the declared cache window when freshness matters. A deployment that never became active cannot be repaired by purging the cache.",
        ["Do not equate a successful build with a public deployment.", "Do not probe only a preview hostname when the release target is production.", "Do not treat one cached response as evidence of worldwide freshness."],
        ["devops/release-evidence-record", "devops/synthetic-transaction-monitoring", "devops/versioned-edge-asset-cache"],
    ),
    lesson(
        "headless-cms-published-content-contract",
        "Headless CMS publishing: define which records become public routes",
        "A CMS record can exist, remain a draft, and still be absent from a public build by design.",
        "A headless publishing contract has at least four identities: CMS record ID, editorial status, public slug, and content revision. The frontend must define whether it reads content at build time, request time, or through a refresh job. A draft or private record should not enter the public route manifest. A published record should have a stable canonical path, validated fields, and a clear policy for slug changes and unpublishing. Pagination is part of correctness; fetching the first page of an API response can silently omit later records. Editorial timestamps alone are not sufficient when updates arrive out of order or a record is deleted.",
        "Suppose the CMS contains 47 published lessons, 6 drafts, and 2 private notes. A publishing job requests all pages of the published collection, verifies that 47 distinct IDs were received, and builds routes from validated slugs. It records the CMS revision used by the build. A new lesson saved as a draft must remain invisible on the public site, even if its slug is known. Publishing it creates a route only after the next successful refresh or deployment; unpublishing removes that route or returns a deliberate gone response under the site's policy. A slug rename needs a redirect plan and a collision check before the old path disappears. Compare route inventory with the CMS inventory after each release.",
        "text",
        "CMS snapshot contract\nPublished IDs received: 47\nDraft records excluded: 6\nPrivate records excluded: 2\nRoute key: validated public slug\nRevision: content snapshot identifier\nFailure: incomplete pagination blocks promotion\nUnpublish: route removed or explicit gone response",
        "Collecting P paginated records is O(P) in data transferred, with one or more network round trips per page. A build-time snapshot gives stable pages but introduces a delay until the next build; request-time reads reduce that delay but shift CMS availability into the reader path. Record the freshness target and choose the architecture against it. Measure missing routes, duplicate slugs, CMS-to-public revision lag, and unpublish lag rather than counting only successful API requests.",
        ["Do not assume that a saved CMS record is published.", "Do not fetch only the first page of a paginated collection.", "Do not let draft or private content leak through a public preview query."],
        ["devops/build-deployment-live-route-evidence", "devops/api-compatibility-window", "devops/event-schema-evolution"],
    ),
    lesson(
        "cms-webhook-replay-reconciliation",
        "CMS webhooks: handle duplicate, reordered, and missing publication events",
        "A webhook should trigger a reconciliation of current state, not be treated as a perfect history.",
        "Webhook delivery can repeat after a timeout, arrive out of order, or disappear during an endpoint outage. Validate the sender using the provider's supported secret or signature scheme, enforce a bounded request size, and acknowledge only after the event is durably accepted. Use an event ID for transport deduplication, but use the CMS record ID and current revision to decide the public state. A replayed publish event must not resurrect a record that was later unpublished. A scheduled inventory comparison repairs events that were never delivered. Keep the event log, refresh job, and site deployment identities separate so an operator can tell which transition failed.",
        "A handbook entry is published at revision 72, edited at 73, and unpublished at 74. The 72 webhook arrives twice; the 73 webhook arrives after the 74 event. A worker stores each accepted event ID once, fetches the record's current CMS state, and computes the route action from revision 74 instead of blindly applying the event payload. If the record is now unpublished, it removes or expires the public route under the publishing contract. Each night, a reconciliation job compares the CMS list of published IDs with the site's route inventory and queues repairs for discrepancies. The operator tests a lost webhook, a repeated webhook, and an out-of-order pair before shipping the integration.",
        "sql",
        "CREATE TABLE cms_event_receipts (\n  event_id text PRIMARY KEY,\n  record_id text NOT NULL,\n  accepted_at timestamptz NOT NULL DEFAULT now()\n);\nINSERT INTO cms_event_receipts (event_id, record_id)\nVALUES ('evt-7284', 'lesson-47')\nON CONFLICT (event_id) DO NOTHING;",
        "The receipt insert has indexed lookup cost near O(log N) for N stored events and storage proportional to retained event IDs. The SQL only deduplicates transport events; it does not decide which revision is public or atomically update a remote site. The worker still must fetch current state, compare revisions, and reconcile uncertain deployments. Keep receipts at least as long as the replay horizon, then bound table growth. Watch event age, signature failures, refresh failures, and inventory differences; webhook success alone cannot prove a live route changed.",
        ["Do not apply a late publish event over a newer unpublish.", "Do not use only in-memory event deduplication.", "Do not treat an HTTP acknowledgement as proof that the public route changed."],
        ["devops/headless-cms-published-content-contract", "devops/transactional-outbox-delivery", "devops/serverless-event-idempotency-ledger"],
    ),
    lesson(
        "content-cache-invalidation-window",
        "Published content caches: bound the stale window and purge the right key",
        "A fresh origin response can coexist with an old public page at the edge or in the browser.",
        "A publishing system may cache HTML, API JSON, redirects, and assets at different layers. Each layer needs an explicit key, lifetime, and invalidation path. An update to a CMS record does not automatically invalidate every rendered URL that mentions it. A changed lesson may affect its canonical page, a topic index, a search feed, and related-lesson cards. Purge only the affected keys when the provider supports it, and use a bounded time-to-live as a recovery path when purge delivery fails. A redirect can introduce another cached location, so test both the requested path and its destination. Keep private or preview responses out of shared caches.",
        "A published guide changes from revision 72 to 73. The origin shows 73, but a reader still sees 72 on the guide path and an index card. The operator inventories both affected URLs, checks cache headers and the actual edge key, and issues an invalidation for those keys. It then probes through the public hostname until both paths return 73 or the documented 900-second maximum age expires. A failed purge does not make stale content permanent because the TTL is bounded. If revision 73 contains a legal correction requiring immediate removal, the operator uses the emergency bypass or temporary route block while invalidation is verified from more than one location.",
        "text",
        "Content revision: 73\nAffected keys: guide route, topic index, search feed\nPublic maximum age: 900 seconds\nPurge receipt: request identity and result\nVerification: route and index show revision 73\nFallback: expiry or emergency bypass",
        "If U rendered URLs depend on one record, precise invalidation is O(U) key operations; broad purges cost fewer commands but increase origin traffic and can create a stampede. Keep a dependency map for high-impact surfaces and measure origin load after purge. A 900-second TTL sets an upper stale bound only when every cache honors it and the origin serves the new version. Monitor CMS-to-edge lag at p95 and the oldest stale route, not just purge API success.",
        ["Do not purge an origin URL while readers use a different edge key.", "Do not cache preview or private responses in a shared layer.", "Do not assume that purging one lesson updates every index that embeds it."],
        ["devops/headless-cms-published-content-contract", "devops/versioned-edge-asset-cache", "devops/edge-cache-privacy-fallback"],
    ),
    lesson(
        "preview-production-environment-boundary",
        "Preview and production publishing: keep content and configuration separate",
        "A preview build needs explicit boundaries for CMS credentials, branch, hostname, and indexing.",
        "A preview environment is a test surface with its own deployment identity and configuration. It may read unpublished content for editorial review, but that access must not turn draft data into a public production route. Separate API credentials, CMS endpoints, and cache namespaces where possible. A preview hostname should not be used as the production smoke target, and a production build should reject preview-only flags. Check which branch or commit triggered the deployment and which configuration values were injected at build time; changing an environment variable after a static build may require another build. Treat preview URLs as potentially shareable unless access controls are actually enforced.",
        "A candidate branch renders a draft lesson for an editor. The preview build uses a restricted draft-reading credential and a preview cache namespace; the production build uses only public published content. Before promotion, a release check compares the branch, deployment ID, CMS mode, and output directory against an expected production manifest. It also probes a draft slug through the public hostname and requires a non-success response. A preview rendering that looks correct is useful evidence for layout and editorial review, but it does not establish that the production deployment received the same content snapshot or that the live route is reachable. Record both observations separately.",
        "text",
        "Environment gate\nPreview: candidate branch, draft-reading credential, isolated cache\nProduction: approved branch, published-only collection\nProduction build assertion: preview flag absent\nPublic draft probe: no successful response\nRelease receipt: deployment ID and CMS snapshot revision",
        "Duplicating builds and cache namespaces increases storage and execution cost, but it prevents a preview-only revision from contaminating production. A credential with draft access expands the blast radius of a leaked preview; scope it to the minimum records and revoke it when the review ends. Checking E environment fields is O(E) local work. The expensive part is proving the resulting public behavior, so include production-route probes and an explicit draft-leak test in the release gate.",
        ["Do not infer production state from a preview deployment.", "Do not ship a draft-reading token in the browser bundle.", "Do not assume a private preview merely because its URL is hard to guess."],
        ["devops/headless-cms-published-content-contract", "devops/build-deployment-live-route-evidence", "devops/secrets-and-configuration"],
    ),
    lesson(
        "web-release-smoke-and-rollback",
        "Web release rollback: check the page graph and preserve content state",
        "Returning to an earlier frontend artifact does not reverse CMS edits or cache entries.",
        "A web release contains more than a homepage. Changed routes, canonical links, navigation edges, sitemap entries, redirects, and the CMS snapshot form a page graph that a visitor and crawler traverse. A smoke test should check the routes affected by the release, verify that their links resolve, and confirm the expected revision. An earlier frontend artifact can be restored quickly, but it may not understand newly published fields or slugs. Maintain a compatibility window and decide whether the recovery action is artifact rollback, CMS correction, cache bypass, or a forward fix. Keep the release record tied to a deployment ID and content snapshot so the team can explain the public state.",
        "A release adds 12 DevOps lessons and changes 4 existing related-lesson cards. The smoke job tests those 16 routes, the DevOps index, and the navigation paths that expose them. It rejects broken internal links, duplicate canonical paths, and a mismatch between route revision and the expected CMS snapshot. After a faulty frontend template is found, traffic returns to the prior artifact. The operator checks that this artifact can still render the 12 new records; if not, it temporarily hides those routes or publishes a compatible forward fix. It also checks edge cache entries created by the faulty template and records any CMS edits that need independent repair. Recovery is finished only after public probes pass.",
        "text",
        "Release 84 smoke scope\nChanged lessons: 12\nChanged related cards: 4\nShared index: 1\nChecks: status, marker, canonical path, internal links\nRollback candidate: prior artifact plus current CMS snapshot\nRecovery evidence: public probes pass after cache window",
        "For V changed pages and E internal links on them, a direct graph smoke costs O(V + E) requests before retries and caching effects. Full-site checking may be suitable overnight, while release gates should cover changed pages plus shared hubs and high-risk routes. A rollback control-plane action may be fast; repair cost grows with incompatible content records and stale caches. Measure broken-link count, missing-route count, CMS-to-public lag, and time until the user path is healthy again.",
        ["Do not declare recovery when only the homepage loads.", "Do not assume a frontend rollback reverses CMS state.", "Do not ignore cached redirects and index pages after a route change."],
        ["devops/build-deployment-live-route-evidence", "devops/content-cache-invalidation-window", "devops/serverless-version-data-rollback"],
    ),
]

project_path = "devops/headless-publishing-release-project"
quiz_path = "quizzes/devops-web-publishing-decisions"
titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
titles[project_path] = "Project: publish, unpublish, and recover a headless learning site"
titles[quiz_path] = "DevOps web publishing decisions"
assert all(item["path"] not in by_path for item in specs)
assert project_path not in by_path and quiz_path not in by_path
assert all(target in titles for item in specs for target in item["related"])


def links(paths):
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in dict.fromkeys(paths)
    ) + "</ul>"


for heading, summary, paths in [
    ("Publishing and CMS state", "Connect build identity, editorial status, and reliable change delivery.", [specs[i]["path"] for i in (0, 1, 2)]),
    ("Public delivery and recovery", "Bound staleness, isolate previews, and verify the page graph after rollback.", [specs[i]["path"] for i in (3, 4, 5)]),
]:
    by_path[course]["data"]["modules"].append({"title": heading, "summary": summary, "lessons": paths})
    by_path[course]["body"] += f"<h2>{html.escape(heading)}</h2><p>{html.escape(summary)}</p>" + links(paths)
by_path[course]["updated_at"] = stamp

for index, item in enumerate(specs):
    path = item["path"]
    row = copy.deepcopy(by_path["devops/continuous-integration"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
               title=item["title"], summary=item["summary"], subject="devops",
               category="DevOps", difficulty="Advanced", tags=["devops", "web-publishing"],
               sort_order=25110 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
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
               summary="Prove published-only routing, webhook replay safety, cache freshness, and a compatible rollback.",
               difficulty="Advanced", sort_order=25190,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 10,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in related_paths]}
project["body"] = (
    "<p>Build a disposable learning site that consumes a test CMS and publishes static routes through a preview and production-like edge. Seed 47 published lessons, 6 drafts, and 2 private notes. A passing project shows all 47 public routes, no public draft routes, a traceable deployment and CMS snapshot, bounded stale content, and a recovery path after a broken frontend template. Keep the test account and cache separate from any live publication account.</p>"
    "<h2>Construct the release record</h2><p>Capture source commit, build artifact digest, output directory, deployment ID, target branch, CMS snapshot revision, and expected route count. Paginate the CMS collection until every published ID is received. Reject duplicate slugs and malformed records before building. Run a public-path smoke check against the production-like hostname; inspect the route body, status, canonical path, and index links. Save probe responses with the release record.</p>"
    "<pre><code class=\"language-text\">Acceptance ledger\nPublished IDs: 47 distinct records\nPublic draft or private routes: 0\nDuplicate webhook effect: 0\nUnpublish propagation: within 900 seconds\nPreview credential in browser bundle: 0\nBroken links in changed page graph: 0\nRollback: prior artifact reads current CMS snapshot</code></pre>"
    "<h2>Inject publication faults</h2><p>Publish a new record, then deliver its webhook twice. Edit and unpublish it; replay the earlier publish event after the unpublish event. The route must follow current CMS state, not the last webhook received. Drop one webhook entirely and run inventory reconciliation to restore parity. Hold an old edge response through one cache cycle, purge the affected route and topic index, and measure the actual stale window. Try a candidate preview with draft access, then prove that the production-like hostname cannot serve its draft slug.</p>"
    "<h2>Recover the public page graph</h2><p>Deploy a faulty template that breaks a related-lesson link. Fail the smoke gate, restore the prior artifact, and verify it can render records already published under the new CMS revision. If it cannot, use a compatible forward fix or hide the incompatible route under the agreed policy. Record the deployment switch, independent CMS state, cache state, and final public probes. The exercise is incomplete if only the homepage passes.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not use a preview URL as production proof.</li><li>Do not let an old event republish a withdrawn lesson.</li><li>Do not claim rollback repaired CMS data or cached pages without probing them.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*related_paths, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Headless publishing release drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("What proves that a new guide is publicly available?", ["A public-route response with expected revision and deployment identity", "A local build exit code", "A pushed commit alone"], "The visitor route is the final delivery boundary."),
    ("A CMS has 47 published records but the build has 20 routes. What should fail?", ["The route inventory gate after complete pagination", "Only the browser console", "Only the preview cache"], "Incomplete pagination is a missing-content release defect."),
    ("A draft record has a known slug. What should the public route do?", ["Remain unavailable under the publishing contract", "Return the draft because its slug is known", "Cache the draft until the next build"], "A slug does not grant publication status."),
    ("An old publish webhook arrives after unpublishing. What state wins?", ["The current CMS status and revision", "The most recently delivered webhook", "The oldest successful deploy"], "Delivery order is not editorial revision order."),
    ("Why keep a scheduled CMS-to-route reconciliation?", ["It repairs missed webhook deliveries", "It removes the need to authenticate webhooks", "It makes every cache immediately fresh"], "Webhooks are a trigger, not a complete audit trail."),
    ("An origin serves revision 73 but the edge serves 72. What should be inspected?", ["The public cache key, TTL, purge result, and affected index routes", "Only the CMS editor screen", "Only the local build log"], "Fresh origin content does not prove edge freshness."),
    ("What bounds staleness when a purge fails?", ["A verified maximum age and fallback bypass policy", "An unbounded cache entry", "A successful webhook acknowledgement"], "Purge needs a bounded expiry fallback."),
    ("A candidate preview shows a draft correctly. What must production still prove?", ["Published-only data and the public route on the production deployment", "That the preview URL is hard to guess", "That the editor saw the draft once"], "Preview success has a different branch and content boundary."),
    ("Where should a draft-reading CMS credential live?", ["Server-side preview configuration with restricted scope", "The public browser bundle", "A shared query parameter"], "A browser bundle cannot keep an editorial credential secret."),
    ("A frontend rollback succeeds while a new CMS field remains. What next?", ["Test old-artifact compatibility with current content and reconcile failures", "Assume CMS data rolled back", "Purge only the homepage"], "Changing artifacts does not reverse editorial state."),
    ("Which routes belong in a changed-content smoke gate?", ["Changed pages, shared indexes, and affected navigation edges", "Only the homepage", "Only the build preview"], "A page graph can fail while the homepage succeeds."),
    ("What release record helps isolate a missing public page?", ["Commit, artifact, deployment, CMS snapshot, and observed route response", "Only the author name", "Only the local terminal timestamp"], "Each boundary needs an identity and observable result."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on CMS state, edge freshness, preview isolation, and public release evidence.",
            sort_order=25200, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in related_paths],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Choose the evidence or recovery action that matches the current publishing boundary. A build, CMS edit, webhook, and public response can each report a different state.</p>"
    "<h2>Review these lessons</h2>" + links(related_paths)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-serverless-operations-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not infer live content from an editor preview.</li><li>Do not treat webhook delivery as page freshness.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Web publishing decisions</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for source, targets in {
    "devops/release-evidence-record": [specs[0]["path"]],
    "devops/api-compatibility-window": [specs[1]["path"]],
    "devops/transactional-outbox-delivery": [specs[2]["path"]],
    "devops/versioned-edge-asset-cache": [specs[3]["path"]],
    "devops/secrets-and-configuration": [specs[4]["path"]],
    "devops/synthetic-transaction-monitoring": [specs[5]["path"]],
    "devops/cross-system-release-project": [project_path],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Web publishing follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1,
                  "total_records": len(rows)}))
