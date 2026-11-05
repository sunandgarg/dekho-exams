"""Add original navigation and delivery projects with explained quiz decisions."""

import copy
import datetime
import html
import json
import subprocess
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
by_path = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def para(value):
    return f"<p>{html.escape(value)}</p>"


def link(path):
    assert path in by_path, path
    return f'<a href="/{html.escape(path, quote=True)}">{html.escape(by_path[path]["title"])}</a>'


projects = [
    dict(path="web-tech/history-safe-review-journey-project", title="Project: history-safe review journey",
         summary="Make a case queue survive direct links, Back, Forward, page restoration, and delayed content.",
         intro="Build a review journey for reviewer 29: filter the queue to Pending, move to page two, open case 47 from row 31, then return with Back. A direct link and a reload must reproduce the filter and case state. A meaningful selection adds one history entry; typing into an uncommitted search does not add twenty entries. The case route places keyboard focus on its heading. Returning to the queue restores a stable row anchor after data and fonts are ready, unless the user has already scrolled. The browser may restore an entire suspended page, so sign-out in a second tab or a changed case version must trigger a fresh authority check before the old action controls are treated as current. A likely future route may be warmed, but private case HTML must not be fetched for every visible link.",
         scope=["Define canonical URL parsing for filter, cursor, and case ID; test direct entry, reload, Back, and Forward under one route model.",
                "Record one stable row anchor and move focus on new navigation; cancel delayed scroll restoration after manual user input.",
                "Handle pageshow restoration and recheck session plus case version before enabling volatile actions.",
                "Limit speculative loading to safe public route assets, with a byte budget and a normal-navigation fallback."],
         code='function mayRestoreQueue(anchor, currentFilter, userMoved) {\n  return Boolean(anchor) && anchor.filter === currentFilter && !userMoved;\n}\nconsole.log(mayRestoreQueue({ filter: "Pending", caseId: 47 }, "Pending", false));\n// Output: true',
         cost="Parsing q URL fields is O(q), and locating a prior row among n rendered rows is O(n) unless an existing row index is available. A stable anchor takes little storage but may require waiting for a delayed queue response; a pixel coordinate is faster to apply and easier to get wrong. Speculating p route resources of average b bytes can spend O(p × b) transfer before any click. Measure first-route timing, back-navigation latency, focus correctness, unused prefetched bytes, and permission-recheck timing together. A fast restored page that advertises an unavailable action fails the project.",
         failure="Push every search keystroke into history and count how many Back presses are needed to leave the queue. Change the account in another tab, return with Back, and verify the restored page does not keep its private action enabled. Delay the queue response until after the user manually scrolls; the old restoration task must not jump the page later. Change row heights with longer translated titles and remove the original anchor row, then inspect the fallback. Hover case 47 without opening it and confirm no private detail request or analytics visit occurs.",
         checks=["Direct links, reload, Back, and Forward reproduce route state without a long typing history.", "Focus enters new content and Back returns near the prior queue row after slow loading.", "A restored page rechecks session and volatile case data before allowing action.", "Speculative work stays within its budget and never fetches every private case."],
         mistakes=["Changing history without updating content.", "Resetting scroll on Back or restoring it after a new manual scroll.", "Treating a suspended page as freshly authorized.", "Prefetching all private case links as a performance shortcut."],
         related=["web-tech/url-state-and-history-entry-contracts", "web-tech/back-forward-cache-and-restored-state", "web-tech/route-scroll-and-focus-restoration", "web-tech/navigation-prefetch-and-private-data-budget", "web-tech/browser-routing-and-history"]),
    dict(path="web-tech/edge-cache-and-critical-resource-project", title="Project: edge cache and critical resource release",
         summary="Ship public guides and private dashboards with correct variants, bounded staleness, and measured image priority.",
         intro="Design the delivery policy for a public inspection guide, its English and Hindi routes, a private case dashboard, a versioned application bundle, and a primary case photograph. The public guide can be cached for a bounded period if an editorial correction can be invalidated across every locale and edge. Its compressed representation must match the client's advertised capability. The private dashboard must never be reused by a shared cache for another account, even when both viewers request the same path. Versioned bundles may live longer because a changed build gets a new URL. The primary photograph must be discoverable early on the route where it appears; offscreen thumbnails should not receive the same priority. Show real response headers, body revisions, and waterfall measurements in the project review.",
         scope=["Classify every response by audience, cache lifetime, representation variants, and invalidation owner before setting edge rules.",
                "Test two accounts and two locales through a warm shared cache, including a 304 response and different encoding capabilities.",
                "Publish guide revision 47, purge all affected variants, and inspect two edge locations before claiming the correction is complete.",
                "Compare cold and warm waterfalls for one primary image plus 18 thumbnails, checking transfer, largest-content timing, and duplicate downloads."],
         code='function mayUseSharedCache(response) {\n  return response.publicContent && !response.accountSpecific && response.variantKeyComplete;\n}\nconsole.log(mayUseSharedCache({ publicContent: false, accountSpecific: true, variantKeyComplete: true }));\n// Output: false',
         cost="A public cache lowers repeated origin work, but every language and content-encoding variant consumes storage and can reduce the hit rate. A purge across e edge locations creates at least O(e) distribution work and may not finish simultaneously. Compressing a b-byte text response costs CPU proportional to its size, while an already-compressed photo may yield little transfer saving. Each unnecessary preloaded image consumes bytes and competes with the current page's critical request. Report hit rate alongside correctness, purge delay, origin load, encoded size, and primary-image request start time; none of those numbers alone proves a good release.",
         failure="Warm the dashboard cache as account 29 and request the same path as account 62. Any copied case count is a policy failure, even if a later client fetch repairs it. Warm the guide in one language and encoding, then request another; a wrong-language page or undecodable bytes exposes an incomplete variant key. Publish a guide correction but purge only one locale, leaving an old checklist elsewhere. Finally mark all images high priority and compare the waterfall with a single primary-image hint. If the primary image URL appears only after JavaScript, move discovery into initial HTML before tuning priority.",
         checks=["No warm shared-cache request leaks a private dashboard across accounts.", "Locales and encodings remain correct through cache hits and validation responses.", "Every public guide variant reaches the intended revision after an observable purge.", "The primary image starts early without turning offscreen thumbnails into competing critical requests."],
         mistakes=["Using a cookie variant as the only protection for private HTML.", "Calling one edge purge globally complete without verification.", "Compressing a response without matching metadata and Vary.", "Giving all images high priority instead of measuring the first visible candidate."],
         related=["web-tech/shared-cache-keys-and-private-response-boundaries", "web-tech/stale-revalidation-and-versioned-purges", "web-tech/content-negotiation-and-compression-contracts", "web-tech/critical-resource-discovery-and-priority", "web-tech/cache-etag-revalidation"]),
]

for number, project in enumerate(projects, start=1):
    assert project["path"] not in by_path
    subprocess.run(["node", "--check", "--input-type=module"], input=project["code"],
                   text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project["path"])),
                 path=project["path"], title=project["title"], summary=project["summary"],
                 sort_order=1090 + number, created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                     "content_format": "html", "seo_ready": False, "kind": "project",
                     "author_path": "authors/aitrove-editorial", "reading_minutes": 8, "related": project["related"]}
    body = para(project["intro"])
    body += "<h2>Build contract</h2><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in project["scope"]) + "</ul>"
    body += '<h2>Implementation checkpoint</h2><pre><code class="language-javascript">' + html.escape(project["code"], quote=False) + "</code></pre>"
    body += "<h2>Cost and boundaries</h2>" + para(project["cost"])
    body += "<h2>Failure drill</h2>" + para(project["failure"])
    body += "<h2>Acceptance checks</h2><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in project["checks"]) + "</ul>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in project["mistakes"]) + "</ul>"
    body += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["related"]) + ".</p>"
    entry["body"] = body
    entries.append(entry)
    by_path[entry["path"]] = entry

quiz_path = "quizzes/web-development-navigation-delivery-decisions"
questions = [
    ("When should a client route create a new history entry?", ["After a meaningful committed navigation", "For every typed search character", "Whenever any component rerenders"], "A history entry should represent a step the user may want Back to undo. Typing and internal rerenders should not fill the Back chain with incidental states."),
    ("What must happen after pushState changes the address?", ["The router must render matching content", "The browser fetches and rerenders automatically", "Authorization becomes permanent"], "pushState updates session history but does not fetch a document or rerender the application. The route owner must update content and later handle Back and Forward traversal."),
    ("What does pageshow with persisted true indicate?", ["The page was restored from a preserved history snapshot", "The server just validated every action", "A new document was always downloaded"], "The old DOM and heap may return quickly from browser memory. Volatile case state and permissions need an explicit recheck even though the page appears immediately."),
    ("What is the safer scroll anchor for a changing queue?", ["A stable row identity with a fallback", "Only a fixed pixel coordinate", "The number of visible buttons"], "Row heights and membership can change while a user is away. A stable content anchor survives many layout changes and can choose a nearby valid row if the original is gone."),
    ("When should a delayed scroll restoration stop?", ["After the user manually scrolls", "Only after the tab closes", "Never, even when it moves the page later"], "A restoration task should not override a later explicit user choice. Cancel or invalidate the pending jump when the person takes control of the viewport."),
    ("Why avoid prefetching every private case link?", ["It spends bandwidth and requests private data before intent is clear", "It makes all links public", "It removes the need for server permission checks"], "A large queue could trigger many unused private reads and compete with the current page. Speculation must stay bounded and cannot replace current authorization."),
    ("What distinguishes a shared edge cache from a browser cache?", ["Its stored response may be served to different viewers", "It can hold only images", "It always verifies every permission"], "Shared cache audience is broader. Account-specific HTML needs a private storage policy so a warm response cannot be reused for another viewer."),
    ("Does Vary: Cookie alone make private HTML safe for shared storage?", ["No; classify the response as private or unstoreable", "Yes, it guarantees every permission check", "Yes, if the URL has a query string"], "A cookie-based variant can create many cache objects and does not express the intended private audience. Set explicit cache ownership and test with two accounts."),
    ("When is stale-while-revalidate suitable?", ["When the content contract allows a bounded old copy", "For every permission decision", "Only after deleting all validators"], "A brief stale public guide may be acceptable, but volatile authority and case actions need current server checks. Choose the window from consequences, not a universal speed target."),
    ("What must a cache know for compressed variants?", ["The selected Content-Encoding and the Vary input", "Only the image filename", "The last user's scroll position"], "A cache must distinguish representations selected by encoding capability, and the client must know how to decode the bytes it receives."),
    ("What should an explicit locale route do when Accept-Language differs?", ["Honor the chosen route locale", "Silently switch to the header language", "Return every language in one body"], "A chosen path is part of navigation identity. Header language can guide an entry decision, but should not silently replace an explicit user-selected locale route."),
    ("Which image should usually avoid lazy loading on the first page?", ["The likely largest visible image", "Every thumbnail below the fold", "An image on a future route"], "The primary visible image needs early discovery. Lazy loading it can delay the largest visible element, while offscreen thumbnails can often wait."),
]

assert quiz_path not in by_path
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: navigation and delivery decisions quiz",
            summary="Twelve explained decisions about browser history, page restoration, private caching, variants, and resource priority.",
            sort_order=1095, created_at=stamp, updated_at=stamp, published_at=stamp)


def quiz_item(index, item):
    prompt, options, explanation = item
    shift = index % len(options)
    return {"prompt": prompt, "options": options[shift:] + options[:shift],
            "answer": (0 - shift) % len(options), "explanation": explanation}


quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes",
                "content_format": "html", "seo_ready": False,
                "questions": [quiz_item(index, item) for index, item in enumerate(questions)]}
quiz["body"] = para(quiz["summary"] + " Choose one response, inspect the explanation, and revisit the lesson for a missed boundary.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for project in projects for path in project["related"][:4]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path["web-tech/web-technology/project"]
project_hub["data"]["modules"][0]["lessons"].extend(project["path"] for project in projects)
project_hub["body"] += "<h2>Navigation and delivery projects</h2><ul>" + "".join(
    f'<li>{link(project["path"])} — {html.escape(project["summary"])}</li>' for project in projects) + "</ul>"
project_hub["summary"] = "Build and verify twenty-two projects across browser, API, data, identity, search, quality, rendering, forms, navigation, delivery, accessibility, privacy, offline, live, and release contracts."
project_hub["updated_at"] = stamp

quiz_hub = by_path["web-tech/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Navigation and delivery checks</h2><p>" + link(quiz_path) + " — " + html.escape(quiz["summary"]) + "</p>"
quiz_hub["updated_at"] = stamp

for hub_path, project_path in [("web-tech/navigation-history-and-page-lifecycle", projects[0]["path"]),
                               ("web-tech/http-delivery-and-cache-ownership", projects[1]["path"])]:
    hub = by_path[hub_path]
    hub["body"] += "<h2>Practice path</h2><p>Build " + link(project_path) + " and check decisions in " + link(quiz_path) + ".</p>"
    hub["updated_at"] = stamp

for entry in entries:
    if entry["type"] != "article" or entry["data"].get("section_path") not in {
        "web-tech/navigation-history-and-page-lifecycle", "web-tech/http-delivery-and-cache-ownership"
    }:
        continue
    project_path = projects[0]["path"] if entry["data"]["section_path"] == "web-tech/navigation-history-and-page-lifecycle" else projects[1]["path"]
    entry["body"] += "<h2>Apply and check</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + ".</p>"
    entry["data"]["related"].extend([project_path, quiz_path])
    entry["updated_at"] = stamp

root_entry = by_path["web-tech/web-technology"]
root_entry["body"] += "<h2>Navigation and delivery practice</h2><p>Apply route and response ownership with " + link(projects[0]["path"]) + " and " + link(projects[1]["path"]) + ".</p>"
root_entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": len(projects), "new_quizzes": 1, "new_questions": len(questions)}))
