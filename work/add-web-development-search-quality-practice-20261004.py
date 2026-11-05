"""Add application-search and capacity practice routes."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
by_path = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def link(path):
    assert path in by_path, path
    return f'<a href="/{html.escape(path, quote=True)}">{html.escape(by_path[path]["title"])}</a>'


def para(value):
    return f"<p>{html.escape(value)}</p>"


projects = [
    dict(path="web-tech/private-case-search-project", title="Project: private case search",
         summary="Build a search route that handles index lag, ranking, filters, cursors, and permission revocation.",
         intro="Build a searchable case queue for two teams and at least 62 seeded cases. The source database remains authoritative. An index worker receives case changes with versions, so a retry of an older event must not roll a record back. The search endpoint accepts a bounded query, region, and status. Exact case IDs lead their own query class, equal scores receive an immutable tie-breaker, and cursors belong to one normalized query and filter set. The current user may see only authorized cases. Check titles, snippets, counts, suggestions, and facets, not merely the list cards. The deliverable is a working route plus an evidence packet for freshness, stable ordering, revocation, and query cost.",
         scope=["Store a durable change record with each case write; index only events newer than the stored case version and measure visible lag.", "Normalize and bound search input, define a ranking policy, and paginate with an opaque cursor bound to filters and sort.", "Apply current record permissions before page selection, counts, snippets, suggestions, and facets; recheck detail and write routes."],
         code='function mayApplyProjection(indexedVersion, eventVersion) {\n  return Number.isSafeInteger(eventVersion) && eventVersion > indexedVersion;\n}\nconsole.log(mayApplyProjection(62, 61));\n// Output: false',
         cost="Indexing adds write work and storage. A rebuild reads O(n) source records plus changes that arrive during the scan. Search ranking and authorization can inspect more candidates than the page size, especially when a team can see only a small fraction of matches. Record per-query candidate counts, response latency, and index lag. A short permission cache may reduce repeated checks but requires a revocation path. Do not lower visibility standards merely to make a benchmark pass.",
         failure="Deliver case 47 updates out of order. Search must keep the latest version. Remove team East access while its index projection stays stale; East must not see the case in any result-derived field. Change North/open to South/open while a page request is pending, and confirm that the old response or cursor cannot contaminate the new result set. Seed tied scores at the page boundary and inspect duplicates or omissions. Finally rebuild the index under writes and compare versions before switching the read alias.",
         checks=["Older index events cannot overwrite newer projections and a rebuild catches up before cutover.", "Exact ID and title tasks return expected leading results with stable tie order.", "Query and filter changes reject old cursors; page boundaries contain no duplicates or gaps.", "Permission revocation hides cards, snippets, totals, facets, and suggestions even with stale indexed metadata."],
         mistakes=["Treating index contents as current permission truth.", "Filtering private rows after limiting a result page.", "Using a cursor with no query or filter binding."],
         related=["web-tech/search-index-freshness-and-rebuilds", "web-tech/search-query-normalization-and-ranking", "web-tech/search-filters-and-result-cursors", "web-tech/search-permissions-and-private-results", "web-tech/record-level-authorization"]),
    dict(path="web-tech/release-evidence-and-capacity-project", title="Project: release evidence and capacity",
         summary="Create a small, repeatable release gate for case review correctness and realistic load.",
         intro="Prepare a release gate for the case-review service. A reviewer searches, opens, adds a note, and resolves a case. Keep pure transition rules under fast unit checks. Use a database test to show that status and note are atomic. Send raw JSON through the authenticated API to verify the contract. In a browser journey, check visible errors, focus, names, and a stable narrow layout. Use deferred responses to force stale request outcomes without sleeps. Then run a nonprivate mixed workload across search, detail, and note writes. State tail-latency and error thresholds before running; a fast mean from one cached route is not enough.",
         scope=["Map each failure to a boundary that can observe it: pure rule, transaction, API, browser task, or loaded service.", "Control response order and rejection with deferred test doubles, then compare their payload contract with a real endpoint.", "Run a mixed workload with offered and completed traffic, per-route tail latency, error rate, and saturation measurements."],
         code='function releaseBudget(report) {\n  return report.searchP95Ms <= 420 && report.writeErrorRate < 0.01 &&\n    report.completedPerSecond >= 47;\n}\nconsole.log(releaseBudget({ searchP95Ms: 390, writeErrorRate: 0.004, completedPerSecond: 49 }));\n// Output: true',
         cost="The pure checks are cheap; real database, browser, and load checks take longer and need stable fixtures. Keep the critical gate small enough to run every change and reserve extended capacity studies for a controlled environment. Screenshot artifacts need deliberate review after design changes. A load generator can also become the bottleneck, so compare offered with completed traffic and inspect its own resource use. Record the environment and data shape beside every capacity claim, including differences from production.",
         failure="Inject a note-write failure after a status update and confirm the transaction rolls back. Make case 62 return before case 47 and then reject the old request; neither old completion should alter the current route. Break the form label and narrow layout to prove semantic and visual checks fail for different reasons. Increase traffic until the connection pool queues work. A release should fail when the predeclared tail or error budget is crossed, even if average latency and total successful request count look acceptable.",
         checks=["A failed note write leaves the case open with no partial resolution.", "Both response orders and an obsolete error leave the current route state intact.", "Keyboard and visual checks catch field-feedback and narrow-layout failures.", "A sustained mixed load reports offered/completed rate, per-operation p95, errors, and saturation against fixed thresholds."],
         mistakes=["Using unit tests as proof of database atomicity.", "Adding sleeps instead of deterministic response controls.", "Accepting screenshot updates without inspecting the changed task.", "Testing only mean latency from a cached route."],
         related=["web-tech/test-boundaries-and-evidence-selection", "web-tech/deterministic-test-doubles-and-fault-injection", "web-tech/accessibility-and-visual-regression-checks", "web-tech/load-tests-and-capacity-budgets", "web-tech/transactions-and-concurrent-writes"]),
]

for number, project in enumerate(projects, start=1):
    assert project["path"] not in by_path
    entry = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project["path"])),
                 path=project["path"], title=project["title"], summary=project["summary"],
                 sort_order=1010 + number, created_at=stamp, updated_at=stamp, published_at=stamp)
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

quiz_path = "quizzes/web-development-search-quality-contracts"
questions = [
    ("Which record is authoritative when the search index lags?", ["The newest search hit", "The source case record", "The browser cache"], 1, "The index is a derived projection. The source record owns case truth, while the index can temporarily lag behind a committed change."),
    ("An older indexing event arrives after a newer one. What should happen?", ["Apply it anyway", "Ignore it using a version comparison", "Delete the case"], 1, "A monotonically increasing source version lets the indexer reject an obsolete event and prevents the projection from moving backward."),
    ("When may readers switch to a rebuilt index generation?", ["As soon as the first records appear", "After source reconciliation and replaying changes from the rebuild window", "After stopping all searches forever"], 1, "A rebuild scan races with source writes. The new generation needs the changes committed during that scan and a reconciliation check before cutover."),
    ("Why add a case ID after the relevance score in sorting?", ["To create a stable tie-breaker", "To grant access", "To reduce all scores to zero"], 0, "Two matches can share the same score. An immutable unique key gives their order a stable final comparison, especially across pages."),
    ("What must a search cursor be bound to?", ["Only the page number", "The full normalized query, filters, and ordering context", "The browser window size"], 1, "A cursor from one query cannot safely continue another. Changes to query, filters, or sort require a restart or a server rejection."),
    ("A revoked private case remains in the index. What must search do?", ["Return its title but block the detail page", "Exclude it from cards and every result-derived field", "Show it only in suggestions"], 1, "A title, snippet, count, facet, or suggestion can reveal private information. Current permission must constrain the search response itself."),
    ("What does a pure transition-rule test fail to prove?", ["The rule output for chosen inputs", "Database atomicity of note and status writes", "A rejected invalid state"], 1, "A pure function can check decisions. It cannot observe whether two database writes commit or roll back together in a real transaction."),
    ("How should a race test control response order?", ["With arbitrary sleeps", "With explicit deferred resolve and reject controls", "By repeating it until it passes"], 1, "Deferred controls force each completion order and failure path. Sleeps consume time and still depend on machine scheduling."),
    ("What cannot a screenshot establish by itself?", ["That a button is visibly clipped", "That a field error is associated and focus reaches it", "That content wraps differently"], 1, "Pixels can reveal layout but not the full semantic and keyboard contract. Pair visual comparison with role, name, association, and focus checks."),
    ("A load report has a good mean but slow tail requests. Which gate helps?", ["A predeclared high-percentile latency threshold", "A larger screenshot", "An unbounded retry loop"], 0, "Tail latency exposes the slow subset that averages can hide. Set the threshold before the run and inspect the operation that breaches it."),
    ("Why compare offered and completed traffic?", ["To detect a client or service that reduces completed work under overload", "To change record permissions", "To avoid measuring errors"], 0, "A closed-loop generator or overloaded service may complete fewer requests as latency rises. Offered and completed rates show that gap."),
    ("Which workload better tests case-service capacity?", ["One cached detail route", "A measured mix of search, detail, and writes with realistic data", "Only a unit test of ranking"], 1, "Routes compete for shared resources. A representative journey mix and data shape reveal bottlenecks that one cached operation cannot expose."),
]

assert quiz_path not in by_path
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: search and quality contracts quiz",
            summary="Twelve explained choices about index consistency, permission-aware retrieval, test boundaries, and capacity evidence.",
            sort_order=1015, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes",
                "content_format": "html", "seo_ready": False,
                "questions": [{"prompt": prompt, "options": options, "answer": answer, "explanation": explanation}
                              for prompt, options, answer, explanation in questions]}
quiz["body"] = para(quiz["summary"] + " Choose one answer, inspect its explanation, then revisit the lesson for any missed boundary.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for project in projects for path in project["related"][:4]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path["web-tech/web-technology/project"]
project_hub["data"]["modules"][0]["lessons"].extend(project["path"] for project in projects)
project_hub["body"] += "<h2>Search and quality projects</h2><ul>" + "".join(
    f'<li>{link(project["path"])} — {html.escape(project["summary"])}</li>' for project in projects) + "</ul>"
project_hub["summary"] = "Build and verify fifteen projects across browser, API, data, identity, search, quality, accessibility, localization, platform, privacy, offline, live, and release contracts."
project_hub["updated_at"] = stamp

quiz_hub = by_path["web-tech/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Search and quality checks</h2><p>" + link(quiz_path) + " — " + html.escape(quiz["summary"]) + "</p>"
quiz_hub["updated_at"] = stamp

for hub_path, project_path in [("web-tech/application-search-and-retrieval", projects[0]["path"]),
                               ("web-tech/quality-and-capacity-engineering", projects[1]["path"])]:
    hub = by_path[hub_path]
    hub["body"] += "<h2>Practice path</h2><p>Build " + link(project_path) + " and check decisions in " + link(quiz_path) + ".</p>"
    hub["updated_at"] = stamp

for entry in entries:
    if entry["type"] != "article" or entry["data"].get("section_path") not in {
        "web-tech/application-search-and-retrieval", "web-tech/quality-and-capacity-engineering"
    }:
        continue
    project_path = projects[0]["path"] if entry["data"]["section_path"] == "web-tech/application-search-and-retrieval" else projects[1]["path"]
    entry["body"] += "<h2>Apply and check</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + ".</p>"
    entry["data"]["related"].extend([project_path, quiz_path])
    entry["updated_at"] = stamp

root_entry = by_path["web-tech/web-technology"]
root_entry["body"] += "<h2>Search and quality practice</h2><p>Apply retrieval and release evidence with " + link(projects[0]["path"]) + " and " + link(projects[1]["path"]) + ".</p>"
root_entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": len(projects), "new_quizzes": 1, "new_questions": len(questions)}))
