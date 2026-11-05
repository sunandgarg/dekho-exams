"""Add linked CMS publishing lessons, project, and review quiz to local drafts."""

import copy
import datetime
import html
import json
import re
import subprocess
import uuid
from pathlib import Path


root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
by_path = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def paragraph(value):
    return "<p>" + html.escape(value) + "</p>"


def link(path):
    assert path in by_path, path
    return '<a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a>"


hub_path = "web-tech/cms-content-publication-and-preview-boundaries"
hub_title = "CMS Content, Publication, and Preview Boundaries"
topics = [
    dict(
        slug="cms-public-content-projection-and-route-identity",
        title="CMS Public Projections and Route Identity",
        summary="Expose only published fields through stable route identities and explicit response contracts.",
        concept="A content management system stores editorial state; a public site serves an admitted projection of that state. The public reader should accept published records only, select a small set of known fields, and convert the CMS record into a site-owned route model. A post ID, slug, status, content revision, and canonical path solve different problems. IDs survive title edits; slugs may be renamed; status controls admission; revisions identify exact content; canonical paths direct users to the chosen public address. Do not hand the entire editorial record to the browser because private notes, draft bodies, custom metadata, or future fields can appear without a frontend change. A read-time filter is still needed even if a CMS query parameter asks for published posts, because the route that returns one record must obey the same rule.",
        case="AI Trove stores an article with ID 447, the slug browser-cache-ownership, a published revision 8, and a draft revision 9 containing an unfinished security note. The public site must keep rendering revision 8 until the editor publishes the next revision. If the frontend fetches the latest record by slug and trusts a local flag, a draft response can reach the page or a search index. If the editor later renames the slug, bookmarks at the former path should receive a deliberate redirect to the one canonical path. An unrelated article must not steal the old slug, and a deleted article must not leave a successful empty page. A route table keyed only by title is insufficient because titles need not be unique and can change for editorial reasons.",
        implementation="Define a public content object whose constructor requires published status and exact fields: stable ID, canonical path, title, summary, approved HTML, revision, and updated time. Keep editorial fields outside this type. Normalize the canonical path once; reject duplicate routes during build or ingestion. Maintain a redirect mapping for changed paths, with a bounded chain and a terminal response for removed content. Sanitize or otherwise constrain approved HTML at the trust boundary rather than assuming every editor role is safe. Treat nested media references and related-lesson routes as dependencies: an article should not link to a route the public reader cannot serve. Return a deliberate 404 for a draft or nonexistent path; reserve a server error for a failed CMS read so monitoring does not mistake an outage for missing content.",
        cost="Fetching only required fields reduces response bytes and client parse work. In a build or warm-up over N records, constructing the route map takes O(N) expected time and O(N) memory with a hash map; collision checks are part of this pass. A direct map lookup is expected O(1), while a remote CMS request adds network latency and must have a deadline. Draft exclusion is a correctness boundary, not a cache optimization. A redirect table adds storage proportional to renamed paths and can accumulate indefinitely without a retirement policy. Separate the public model from editor permissions so the cache can hold published responses without storing hidden fields. Measure response width, missing-path rate, redirect chains, and stale revision age.",
        failure="Publish revision 8, save an unpublished revision 9, and request the article through the public route, search document builder, and related-card builder. Each must still use revision 8. Force the CMS API to return a private metadata field and verify the public projection drops it. Create two records with the same canonical path and make ingestion fail rather than choose whichever arrives last. Rename a slug twice and verify the oldest address resolves to one canonical destination without a loop. Unpublish a previously public page and make the public route and navigation list withdraw it. Finally, interrupt the CMS request and confirm the failure is logged as an upstream outage rather than silently converted to a 404.",
        drill="Build a small route materializer for three article records: one published, one draft, and one renamed. Accept only the published record into the route map and expose only the public fields. Keep a separate old-path redirect map with loop rejection. Feed the result to a page renderer and a search-index builder, then compare their admitted IDs and revisions. Add a second record with a conflicting path and require a hard validation error. Repeat with malformed HTML and an unresolved related route. Record which errors block publication and which can be reported for editorial repair without hiding a valid older revision.",
        decision="The CMS owns editorial state; the public site owns a narrow, versioned route model and rejects any unapproved revision.",
        code='''function publicArticle(record) {
  if (record.status !== "publish") return null;
  const canonicalPath = `/web-tech/${record.slug}`;
  return Object.freeze({
    id: record.id,
    canonicalPath,
    revision: record.publishedRevision,
    title: record.title,
    summary: record.summary
  });
}

const editorialRecord = {
  id: 447, slug: "browser-cache-ownership", status: "publish",
  publishedRevision: 8, title: "Browser Cache Ownership",
  summary: "Assign each response a cache owner.", privateNote: "Draft review"
};
console.log(publicArticle(editorialRecord));''',
        checks=["Draft revisions never enter public cards or search documents.", "Duplicate canonical paths fail validation before serving.", "Private CMS fields are absent from the response object."],
        mistakes=["Using a slug as a stable record identity.", "Passing the entire CMS object into a public component.", "Turning upstream read failures into missing-page responses."],
        related=["web-tech/content-discovery-and-structure", "web-tech/server-rendering-and-client-data-flow", "web-tech/api-contract-evolution-and-client-migration"],
    ),
    dict(
        slug="cms-draft-preview-authorization-and-cache-isolation",
        title="CMS Draft Preview Authorization and Cache Isolation",
        summary="Bind preview access to a caller and revision while preventing private responses from reaching shared caches.",
        concept="A preview route intentionally renders content that the public reader must reject. It needs a separate authenticated or narrowly scoped access path, a specific revision, and a no-store response policy. A random-looking URL alone is not sufficient if it is long-lived, reusable, or copied into logs and referral headers. The preview service should confirm the editor's current permission for the record, then fetch the requested revision from a privileged CMS connection kept on the server. The public page must not load draft data through the same cache key used for published content. Preview markup can reuse the public renderer, but data admission, authorization, cache headers, and search visibility must remain separate.",
        case="Editor 47 previews revision 9 of article 447 while revision 8 remains public. A CDN cache ignores the query string and stores the preview response under the normal article path. The next anonymous visitor receives unfinished text. A second implementation sets noindex in the HTML yet still allows the shared cache to store the body, so the leak remains. A third sends a preview token to browser analytics through the page URL. The repaired flow checks an editor session, record permission, and revision, obtains content server-side, sets no-store on every preview response, omits third-party scripts where possible, and keeps published pages on separate keys. Revoking access immediately blocks another preview request, even if the editor saved the URL earlier.",
        implementation="Use a server-controlled preview endpoint whose input names record ID and revision but does not itself grant access. Authenticate the caller and check edit permission on that record for each request. If a signed short-lived capability is used for a cross-domain preview, bind its audience, record ID, revision, expiry, and nonce, and verify it server-side; do not treat a generic signed slug as adequate. Exclude preview responses from shared caches and service-worker offline stores. Send Cache-Control: private, no-store and prevent indexing, but regard these headers as defense in depth rather than substitutes for authorization. Keep draft HTML out of page metadata, feed generation, and prefetch targets. Preview must not mutate publication state or purge the public cache.",
        cost="Permission checks and privileged revision fetches cost at least one CMS or database read per preview unless the server has a correctly scoped private cache. That is acceptable for a low-volume editor path; sharing a public cache to save this read is the wrong trade. A signed capability adds verification work and a replay window until expiry unless it is one-time or revocable. A session-based preview avoids a shareable secret but requires editor login on the preview domain. Limit response size and rendering time for malformed drafts, and time out CMS calls. Measure forbidden attempts, preview failures, and accidental cache hits without logging raw capability tokens. The public page's steady-state latency should be independent of preview traffic.",
        failure="Request revision 9 anonymously, as an editor lacking article 447 permission, as editor 47, and after editor 47 loses permission. Only the authorized current session may see it. Inspect the response headers at the origin and CDN; no shared cache should store the draft. Prime the public revision 8 first, preview revision 9, then request the public path anonymously and assert revision 8 still appears. Inspect rendered HTML for third-party requests, canonical URLs, JSON metadata, and link previews that could carry the preview credential. Try an expired capability and a capability for another article or revision. Simulate a CMS timeout and return a private error response without falling back to another editor's draft.",
        drill="Create a preview service for article 447 with two revisions. Keep the public reader unprivileged. Pass a reviewer identity into the preview handler, check a case-specific edit grant, and retrieve the requested draft through a server-only CMS client. Emit no-store and noindex, disable shared caching, and render a visible preview label so editors can distinguish it from the public page. Add a test proxy that deliberately ignores query strings and show that the published path never handles draft requests. Exercise revoked permission, a missing revision, a replayed or expired capability, and a failure in the privileged CMS connection.",
        decision="Preview is a private content read with revision-specific permission; it is not a temporary form of publication.",
        code='''function previewDecision({ editorId, articleId, revision, grants }) {
  const permitted = grants.some(grant =>
    grant.editorId === editorId && grant.articleId === articleId
  );
  return {
    allowed: permitted && Number.isInteger(revision) && revision > 0,
    cacheControl: "private, no-store",
    robots: "noindex, nofollow"
  };
}

console.log(previewDecision({
  editorId: 47, articleId: 447, revision: 9,
  grants: [{ editorId: 47, articleId: 447 }]
}));''',
        checks=["Every preview request rechecks permission for the exact record.", "A preview response never populates a shared public cache key.", "The public route keeps serving its last published revision."],
        mistakes=["Relying on noindex to protect confidential draft content.", "Using a long-lived preview URL as the sole authorization proof.", "Reusing the public cache key for preview data."],
        related=["web-tech/authorization-and-tenant-boundaries", "web-tech/http-delivery-and-cache-ownership", "web-tech/browser-security-and-data-stewardship"],
    ),
    dict(
        slug="cms-media-variants-alt-text-and-asset-ownership",
        title="CMS Media Variants, Alt Text, and Asset Ownership",
        summary="Publish bounded media metadata with stable assets, useful alternatives, and deliberate retention.",
        concept="An editorial image is more than a URL. A public record may need a stable media ID, source dimensions, responsive variants, crop behavior, alternative text, decorative intent, caption, rights state, and publication status. The renderer must choose a variant that fits the layout without silently replacing the editor's meaningful crop. Text alternatives describe the image's function in context, not its file name. Private uploads must remain outside the public media path until publication grants access. A CMS attachment can be referenced by multiple articles, so deleting one post must not blindly delete the underlying bytes. Conversely, replacing an image should not leave unbounded orphaned variants or stale cached assets without a retention rule.",
        case="Article 447 uses a 2600-pixel inspection diagram and a 640-pixel crop for a card. The card crop hides a numbered annotation that the full page relies on, so the same alternative text cannot serve both contexts. A second article references the same full image. An editor replaces the source, but the frontend keeps the old CDN URL and mixes the new caption with old pixels. A draft upload is accidentally exposed through a predictable public attachment URL. The corrected model records asset ID and version, intended usage, dimensions and variant URLs, context-specific text alternatives, and publication scope. The card either receives an approved crop with its own description or uses the full image. Old assets retire only after reference and cache windows are understood.",
        implementation="Store media references in the article revision rather than embedding arbitrary raw upload URLs throughout HTML. Validate MIME type, dimensions, byte size, and actual decoded format before accepting a variant. Give a public asset an immutable versioned URL or a content digest so a new image cannot be confused with old cached bytes. Generate width descriptors from real output dimensions; do not label a 640-pixel file as 1280 pixels. Reserve width and height or an aspect ratio in the page so image loading does not shift content. Ask for alt text at the placement level when the meaning differs by use, while allowing a decorative image to use an empty alternative. Track whether a draft asset is publicly reachable by its storage policy, not merely whether a CMS post is draft.",
        cost="Generating V variants for N source images costs work proportional to decoded pixels and encoded output sizes; a naive build can multiply storage by N times V. Serving an appropriately sized variant reduces transfer bytes and decode work on narrow screens, but too many widths fragment caches. A reference index from media ID to published article revisions takes additional storage and update work, yet makes safe retirement decisions possible. Immutable asset URLs simplify cache correctness because a published revision names exact bytes. Long retention increases storage cost; early deletion can break cached pages and backlinks. Measure variant bytes, largest image render timing, 404s for media, and orphaned asset age. Avoid claiming one image format is always best without target-browser and quality tests.",
        failure="Upload a file whose extension says one format but whose decoded bytes say another, and reject it before publication. Ask for a card crop with a missing annotation, then verify its alternative text and caption still convey the necessary information. Render a 640-pixel variant in a high-density 1280-pixel slot and inspect whether the chosen variant is large enough without sending the 2600-pixel original to every device. Replace the image while a CDN cache holds the old URL; the new article revision must point to a new versioned asset. Delete one of two referencing articles and verify the shared asset remains. Unpublish the final reference, wait through the stated retention period, and only then retire the bytes and variants.",
        drill="Model two articles sharing media ID 83 and one unpublished upload 91. Build a reference list for published revisions, then calculate which assets may be served publicly and which are candidates for retirement. Provide two variants with true intrinsic dimensions and a distinct card crop. Render a card and article using their own text alternatives. Update the source and create a new asset version; keep the old version available while published revision 8 still references it. Add a validation failure for an empty alternative on an informative image, a false width descriptor, and a draft object with a public storage URL.",
        decision="A media reference binds content, meaning, and exact bytes; lifecycle decisions follow published references, not upload filenames.",
        code='''function publicAsset(media, placement) {
  if (!media.published || !media.variants[placement]) return null;
  const variant = media.variants[placement];
  return {
    assetId: media.id,
    version: media.version,
    width: variant.width,
    height: variant.height,
    alt: variant.decorative ? "" : variant.alt
  };
}

const inspectionDiagram = {
  id: 83, version: 4, published: true,
  variants: { card: { width: 640, height: 400,
    decorative: false, alt: "Two marked inspection zones" } }
};
console.log(publicAsset(inspectionDiagram, "card"));''',
        checks=["Every width descriptor matches the actual variant bytes.", "Published revisions reference exact media versions.", "Shared assets survive removal of only one referencing article."],
        mistakes=["Using the filename as alt text.", "Serving draft uploads from public object storage by predictable URL.", "Deleting shared media when one article is unpublished."],
        related=["web-tech/accessible-content-and-media", "web-tech/file-ingestion-and-private-asset-lifecycle", "web-tech/browser-performance-diagnosis-and-measurement"],
    ),
    dict(
        slug="cms-publish-events-cache-search-and-rollback",
        title="CMS Publish Events, Cache, Search, and Rollback",
        summary="Reconcile a publication revision across routes, caches, search, and linked navigation.",
        concept="Publication changes more than one page body. A new approved revision can affect the article route, cards that summarize it, related lessons, category listings, site search, feeds, and a sitemap. A CMS status update does not make all these downstream views change atomically. The system needs a durable publication identity and a reconciliation process that can repeat work safely. Treat a publish event as a desired-state signal: consumers should read the current published revision, update only projections they own, and ignore an older event after a newer revision has arrived. A rollback is a new publication transition that points public readers to an earlier approved body; it still needs cache and search reconciliation.",
        case="Editor 47 publishes revision 9 of article 447. The article route updates, but a category card still shows revision 8 and search returns revision 7. A purge request times out, so the publisher cannot tell whether the CDN accepted it. Retrying blindly with a stale payload could even restore an older search document. The repaired workflow records the article ID, new publication revision, status, and affected route dependencies. A worker can retry invalidation under that identity, while each projection checks the current published revision before writing. A reader may briefly see mixed versions, so the team defines an acceptable lag and records it. If revision 9 contains a mistake, publishing approved revision 8 again creates revision 10 as the new public decision rather than pretending the earlier transition never occurred.",
        implementation="Commit the CMS publication change and a durable change record in the same persistence boundary when the CMS permits it; otherwise reconcile from a periodic scan of current published revisions. Assign a monotonic publication version per article. Maintain a dependency index from article ID to canonical route, old-path redirects, category cards, related cards, feed segments, and search documents. A worker reads the current version, rebuilds those targets, and invalidates cached responses by exact path or versioned key. Make retries idempotent and keep a dead-letter or repair queue for repeated failure. Unpublishing must remove search and listings as well as the route. Do not rely on a single webhook delivery as the only record of the change; webhooks can be duplicated, delayed, or lost.",
        cost="One publish event can fan out to D dependent surfaces. Rebuilding only known dependencies costs work proportional to D rather than re-rendering the whole site, but keeping the dependency index correct adds write and audit work. A versioned cache key avoids ambiguous purge completion but retains older objects until expiry. Path purges reduce retained bytes but can fail independently across regions. Search indexing is usually asynchronous, so query results may lag the article route; the service should measure that delay and decide a reasonable budget. A full reconciliation scan over N articles is O(N) and may be scheduled off the request path. Preserve enough event and projection state to diagnose which surface is stale without storing unpublished bodies in a public log.",
        failure="Deliver publish events for revisions 8, 9, and 10 out of order, then assert every consumer ends at the current published version. Send the same revision twice and verify it does not duplicate a search document or purge job. Fail the CDN purge after the CMS commit and confirm the repair worker can retry; fail the webhook entirely and confirm a revision scan discovers the change. Unpublish the page and check route, cards, search, feed, and sitemap. Rename its path and verify redirects and old caches do not revive an obsolete body. Publish a rollback revision and verify the public version increases even though its approved text comes from an older body. Measure how long each surface remains stale.",
        drill="Build a small publication ledger for article 447. Record revision 8 as public, publish revision 9, then deliver events in the order 9, 8, 9. A search consumer should apply only the current published version. Record affected routes and verify the category card, related card, route, and search document all converge after retries. Simulate a lost webhook and discover revision 10 through a periodic reconciliation pass. Add an unpublish transition and a rollback that republishes approved revision 8 as a new public version. Report last applied version and lag for each projection rather than returning success merely because the CMS save completed.",
        decision="A successful CMS save begins publication; versioned reconciliation makes every public projection catch up and exposes failures.",
        code='''function applyPublication(current, event, document) {
  if (event.version !== current.version) return document;
  if (document && document.version >= event.version) return document;
  if (current.status !== "publish") return null;
  return { articleId: current.id, version: current.version, title: current.title };
}

const current = { id: 447, version: 9, status: "publish", title: "Cache ownership" };
let searchDocument = applyPublication(current, { version: 9 }, null);
searchDocument = applyPublication(current, { version: 8 }, searchDocument);
console.log(searchDocument);''',
        checks=["An older event cannot overwrite a newer public projection.", "Lost webhooks are recoverable by comparing current published revisions.", "Unpublish withdraws the route and each discovery surface."],
        mistakes=["Equating CMS save success with complete public publication.", "Reapplying an old event payload without checking current revision.", "Purging only the article route while leaving cards and search stale."],
        related=["web-tech/http-delivery-and-cache-ownership", "web-tech/content-discovery-and-structure", "web-tech/background-workflow-reliability"],
    ),
]


assert hub_path not in by_path and len(topics) == 4
hub = copy.deepcopy(by_path["web-tech/fastapi-contract-and-resource-boundaries"])
hub.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + hub_path)), path=hub_path, title=hub_title,
           summary="Keep public content, editor previews, media versions, and publication projections on explicit boundaries.",
           sort_order=3760, created_at=stamp, updated_at=stamp, published_at=stamp)
hub["data"] = {"subject_root": "web-tech/web-technology", "section_path": hub_path, "content_format": "html",
               "seo_ready": False, "modules": [], "resource_tabs": [
                   {"title": "Web Development", "path": "web-tech/web-technology"},
                   {"title": "Projects", "path": "web-tech/web-technology/project"},
                   {"title": "Quizzes", "path": "web-tech/quizzes"}]}
entries.append(hub)
by_path[hub_path] = hub

for number, topic in enumerate(topics):
    path = "web-tech/" + topic["slug"]
    assert path not in by_path
    subprocess.run(["node", "--check"], input=topic["code"], text=True, check=True, capture_output=True)
    entry = copy.deepcopy(by_path["web-tech/trace-context-across-request-and-job"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                 title=topic["title"], summary=topic["summary"], sort_order=3761 + number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    related = [hub_path] + ["web-tech/" + other["slug"] for other in topics if other is not topic] + topic["related"]
    body = paragraph(topic["concept"]) + "<h2>Working case</h2>" + paragraph(topic["case"])
    body += '<h2>Implementation boundary</h2><pre><code class="language-javascript">' + html.escape(topic["code"], quote=False) + "</code></pre>" + paragraph(topic["implementation"])
    body += "<h2>Cost and boundaries</h2>" + paragraph(topic["cost"]) + "<h2>Failure trace</h2>" + paragraph(topic["failure"])
    body += "<h2>Verification</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in topic["checks"]) + "</ul>"
    body += "<h2>Practice drill</h2>" + paragraph(topic["drill"]) + "<h2>Decision note</h2>" + paragraph(topic["decision"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in topic["mistakes"]) + "</ul>"
    entry["body"] = body
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": hub_path,
                     "content_format": "html", "seo_ready": False, "kind": "tutorial",
                     "author_path": "authors/aitrove-editorial", "reading_minutes": 8, "related": related}
    entries.append(entry)
    by_path[path] = entry

for topic in topics:
    entry = by_path["web-tech/" + topic["slug"]]
    entry["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in entry["data"]["related"]) + ".</p>"
hub["data"]["modules"] = [{"title": hub_title, "summary": hub["summary"],
                           "lessons": ["web-tech/" + topic["slug"] for topic in topics]}]
hub["body"] = paragraph("A CMS is an editorial system with drafts, revisions, permissions, and attached media. A public site consumes only an approved view. The four lessons follow one article from a versioned public route through a private preview, an exact media asset, and a publication event that must reach caches and discovery surfaces. Each page gives an operational failure, a bounded implementation, checks, and links to adjacent Web Development topics.")
hub["body"] += "<h2>Topics in this track</h2><ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
hub["body"] += "<h2>Prerequisite paths</h2><p>" + "; ".join(link(path) for path in ["web-tech/content-discovery-and-structure", "web-tech/http-delivery-and-cache-ownership", "web-tech/authorization-and-tenant-boundaries"]) + ".</p>"
curriculum = by_path["web-tech/web-technology"]
curriculum["data"]["modules"].append({"title": hub_title, "summary": hub["summary"],
                                       "lessons": [hub_path] + ["web-tech/" + topic["slug"] for topic in topics]})
curriculum["body"] += "<h2>" + link(hub_path) + "</h2>" + paragraph(hub["summary"]) + "<ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
curriculum["updated_at"] = stamp
crosslinks = {
    "web-tech/content-discovery-and-structure": [hub_path, "web-tech/cms-publish-events-cache-search-and-rollback"],
    "web-tech/http-delivery-and-cache-ownership": ["web-tech/cms-draft-preview-authorization-and-cache-isolation", "web-tech/cms-publish-events-cache-search-and-rollback"],
    "web-tech/accessible-content-and-media": ["web-tech/cms-media-variants-alt-text-and-asset-ownership"],
    "web-tech/authorization-and-tenant-boundaries": ["web-tech/cms-draft-preview-authorization-and-cache-isolation"],
    "web-tech/background-workflow-reliability": ["web-tech/cms-publish-events-cache-search-and-rollback"],
}
for path, targets in crosslinks.items():
    by_path[path]["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    by_path[path]["updated_at"] = stamp

project_path = "web-tech/cms-publication-reconciliation-project"
quiz_path = "quizzes/web-development-cms-publication-contracts"
project = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: CMS Publication Reconciliation",
               summary="Build a public projection, private preview, media ledger, and repeatable publication repair path.",
               sort_order=3765, created_at=stamp, updated_at=stamp, published_at=stamp)
lessons = ["web-tech/" + topic["slug"] for topic in topics]
project["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                   "content_format": "html", "seo_ready": False, "kind": "project", "author_path": "authors/aitrove-editorial",
                   "reading_minutes": 10, "related": [hub_path] + lessons}
project["body"] = paragraph("Build a CMS-backed knowledge site for article 447. Revision 8 is public; revision 9 is an editor draft. Public routes, cards, and search must admit only approved revision 8. Editor 47 may preview revision 9 through a private response, while editor 81 may not. Media ID 83 has versioned article and card variants; draft media ID 91 is inaccessible to public readers. Publishing revision 9 creates one durable publication identity that each route, card, search document, and feed projection can reconcile. The work is complete only when a repeated or lost event cannot leave an older version as the final state.")
project["body"] += "<h2>Build contract</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "Construct a public response from explicit approved fields and fail duplicate canonical routes.",
    "Keep preview authorization, revision fetch, and no-store behavior outside public cache keys.",
    "Bind article revisions to exact media versions and validate variant dimensions and alternatives.",
    "Record publication versions, repair missed notifications, and reject stale projection updates.",
    "Reconcile unpublish, path rename, and rollback across routes and discovery surfaces.",
]) + "</ul>"
checkpoint = '''function shouldApply(currentVersion, incomingVersion, appliedVersion) {
  return incomingVersion === currentVersion && incomingVersion > appliedVersion;
}
console.log(shouldApply(9, 8, 7));
console.log(shouldApply(9, 9, 7));'''
assert subprocess.run(["node", "-e", checkpoint], capture_output=True, text=True, check=True).stdout.strip() == "false\ntrue"
project["body"] += '<h2>Implementation checkpoint</h2><pre><code class="language-javascript">' + html.escape(checkpoint, quote=False) + "</code></pre>"
project["body"] += "<h2>Cost and boundaries</h2>" + paragraph("A route map over N public records takes O(N) expected build time and memory. A published route lookup is expected O(1) after materialization, while a live CMS call adds network time and a failure mode. Media variants cost storage and encoding work proportional to their actual bytes; a reference ledger is needed before retiring shared assets. One publication update fans out to D dependent surfaces. A targeted dependency index bounds that work by D but must itself be kept current. A preview may spend an extra permission and revision read because its low-volume editor path should never borrow a shared public cache. Define lag budgets for card and search updates rather than assuming all surfaces change atomically.")
project["body"] += "<h2>Failure drill</h2>" + paragraph("Save revision 9 without publishing and probe public route, cards, search, feeds, and cache. Try preview as both editors and anonymously. Make a proxy ignore query strings and verify the draft cannot poison the public key. Replace shared media 83 while one published article still references its older version. Publish 9, deliver event 8 after 9, duplicate 9, and lose the webhook for revision 10; a reconciliation scan must recover. Unpublish, rename the canonical path, and republish earlier approved text as a new rollback version. Inspect stale duration and repair state for each projection. A CMS timeout must not become a false 404.")
project["body"] += "<h2>Acceptance checks</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "Anonymous readers never receive a draft or private media object.",
    "Preview permission and cache isolation hold after access is revoked.",
    "Older events and duplicate deliveries cannot lower a projection's applied version.",
    "A missed notification can be repaired from current published state.",
]) + "</ul>"
project["body"] += "<h3>Common Mistakes</h3><ul><li>Testing draft privacy only in the article route, not in cards and search.</li><li>Using noindex as the only preview control.</li><li>Retiring a media object while another revision still references it.</li><li>Treating one webhook as a complete publication transaction.</li></ul>"
project["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["data"]["related"]) + ".</p>"
entries.append(project)
by_path[project_path] = project

questions = [
    ("What can a public article projection include?", ["Only explicitly approved public fields", "Every field returned by the editor API", "The latest draft body when the title matches"], "An allowlisted response contract prevents new private editorial fields from appearing in a public page or search document."),
    ("Why use a stable article ID as well as a slug?", ["A slug can change while the record identity persists", "IDs always encode the author name", "Slugs guarantee uniqueness across all history"], "A rename changes the address; stable identity lets redirects and revision tracking continue to refer to the same record."),
    ("What should happen when two records claim one canonical path?", ["Reject the collision during ingestion", "Serve whichever record arrives last", "Concatenate their HTML"], "A duplicate route is an integrity error; silently choosing one makes publication order affect which article readers see."),
    ("What grants draft preview access?", ["Current permission for the exact record and revision", "A noindex header alone", "Knowledge of the public slug"], "Preview is a private read. The server must authenticate and authorize the editor for the requested article and revision."),
    ("Why separate preview and public cache keys?", ["To keep draft bytes out of a shared public response", "To make drafts searchable", "To skip revision checks"], "A shared key can serve a cached preview to an anonymous reader even when the preview HTML carries noindex metadata."),
    ("What must a short-lived preview capability bind?", ["Audience, record, revision, and expiry", "Only a title string", "Only a CDN region"], "A capability for one draft should not authorize a different article, revision, recipient, or unlimited future access."),
    ("Why identify a media asset version in the article revision?", ["So the revision points to exact bytes despite cache retention", "So alt text may be omitted", "So every upload is immediately public"], "Immutable or versioned assets prevent an old cached image from being mixed with a newly published caption and content state."),
    ("When is a shared asset safe to retire?", ["After published references and retention windows no longer need it", "When any one article is unpublished", "When its filename changes"], "Media may be referenced by several published revisions, so removal follows the reference ledger and cache retention policy."),
    ("What should a responsive width descriptor represent?", ["The actual intrinsic width of that variant", "The original camera width for every crop", "A guessed viewport width"], "A false descriptor can make the browser choose an unsuitable file and breaks the expected transfer and sharpness behavior."),
    ("How should a consumer handle an old publish event?", ["Compare with the current published version before applying", "Overwrite the newer search document", "Delete the article unconditionally"], "Delayed events are normal; reading the current publication state prevents an older payload from lowering the public version."),
    ("What repairs a completely missed webhook?", ["A scan that reconciles current published revisions", "A browser refresh alone", "A longer preview URL"], "A periodic comparison can find publication versions whose downstream projections were never updated by an event delivery."),
    ("What is a rollback in a versioned publication model?", ["A new public transition pointing to earlier approved content", "Erasure of all later event history", "A draft preview served to everyone"], "Publishing an earlier approved body under a new version lets consumers converge without pretending the intervening publication never occurred."),
]
assert len(questions) == 12
balanced = []
for number, (prompt, options, explanation) in enumerate(questions):
    answer = number % 3
    reordered = [options[1], options[2]]
    reordered.insert(answer, options[0])
    balanced.append({"prompt": prompt, "options": reordered, "answer": answer, "explanation": explanation})
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: CMS publication contracts",
            summary="Twelve explained decisions about public projections, previews, media, and publication repair.",
            sort_order=3766, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes", "content_format": "html",
                "seo_ready": False, "questions": balanced}
quiz["body"] = paragraph(quiz["summary"] + " Choose an answer, inspect the reason, and return to the related failure drill.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in [hub_path] + lessons + [project_path]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

for index_path, heading, target in [
    ("web-tech/web-technology/project", "CMS publication project", project_path),
    ("web-tech/quizzes", "CMS publication check", quiz_path),
]:
    index = by_path[index_path]
    index["data"]["modules"][0]["lessons"].append(target)
    index["body"] += "<h2>" + heading + "</h2><p>" + link(target) + " — " + html.escape(by_path[target]["summary"]) + "</p>"
    index["updated_at"] = stamp
hub["body"] += "<h2>Practice and check</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + ".</p>"
hub["updated_at"] = stamp
for path in lessons:
    lesson = by_path[path]
    lesson["body"] += "<h2>Apply and check</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + ".</p>"
    lesson["data"]["related"].extend([project_path, quiz_path])
    lesson["updated_at"] = stamp
curriculum["body"] += "<h2>CMS publication practice</h2><p>" + link(project_path) + "; " + link(quiz_path) + ".</p>"
curriculum["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": 1, "new_lessons": 4, "new_projects": 1, "new_quizzes": 1,
                  "prose_words": {topic["slug"]: len(re.findall(r"\b[\w'-]+\b", " ".join(str(topic[key]) for key in ("concept", "case", "implementation", "cost", "failure", "drill", "decision", "summary")))) for topic in topics}}))
