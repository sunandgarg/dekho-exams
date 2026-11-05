"""Add original location-aware dispatch prompt lessons, project, and quiz."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
lookup = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
subject_root = "prompt-engineering/prompt-engineering"
applications = "prompt-engineering/applications"
production = "prompt-engineering/production"
projects = "prompt-engineering/projects"
quizzes = "prompt-engineering/quizzes"
project_path = "prompt-engineering/quartz-dispatch-route-review-project"
quiz_path = "quizzes/prompt-engineering-location-dispatch"

specs = [
    dict(slug="location-prompt-address-ambiguity-and-identity", title="Location prompts: resolve ambiguous addresses before routing", section=applications,
         summary="Separate user-entered address text from a verified stop identity.",
         definition="A location-aware prompt should not turn a free-text address into a route stop without validation. The application supplies candidate matches with address components, service area, match quality, and stable place identity. The prompt can compare candidates and ask a focused question, but a partial match or a nearby street is not the requested destination. Preserve the original address text next to the chosen candidate for review. A person's name or business label does not prove which entrance a vehicle can use. If the result is ambiguous, mark the stop unresolved and exclude it from a supposedly final route until a trusted user or authoritative record selects it.",
         case="A fictional Quartz Field Service ticket lists '47 Harbor Lane, North Pier' for job J-47. The lookup returns two candidates: a full street-address match in North Pier and a partial match for Harbor Road in another district. The dispatcher selects the first candidate after checking the ticket's depot and entrance note. A different ticket says only 'Harbor Lane' and produces three plausible results; the assistant asks for a street number instead of choosing the nearest one. It keeps job IDs separate from map labels so a similar-looking address cannot silently become another customer's stop.",
         sample="J-47 text: 47 Harbor Lane, North Pier.\nCandidate P-47: full street match, correct service area.\nCandidate P-71: partial street match, wrong district.\nDecision: use P-47 after dispatcher review.\nUnnumbered Harbor Lane ticket: unresolved, no final route.",
         cost="Checking C candidates per stop across S stops is O(SC) comparison work, usually small beside route computation. An extra clarification can delay dispatch, but routing to the wrong street can consume a whole service window. Keep candidate payloads narrow: the address components, match quality, and access point needed for the task. Do not copy unrelated place metadata or private customer notes into the prompt merely because a geocoder returned them.",
         mistakes=["Do not treat a partial address match as verified destination identity.", "Do not choose the nearest candidate merely because it is first.", "Do not merge two jobs because their map labels look similar."],
         related=["prompt-engineering/browser-target-grounding-and-stale-state", "prompt-engineering/clarification-versus-assumption-gate", "prompt-engineering/dataset-intake-column-contract"]),
    dict(slug="location-prompt-coordinate-order-and-precision", title="Location prompts: validate coordinates, units, and precision", section=applications,
         summary="Check latitude-longitude order and avoid false precision in location claims.",
         definition="A coordinate pair needs a declared order, numeric range, coordinate system, and acquisition method. A prompt should not infer that the first number is latitude just because many examples use that order. A point may represent a building centroid rather than the service entrance, so an apparently precise map pin can still be operationally wrong. Store an accuracy or confidence field separately from the coordinate value. When a location is sensitive, pass only the precision necessary for the task and keep exact points out of public summaries. The application validates coordinate fields before they enter route calculations.",
         case="Quartz receives a depot point in latitude-longitude order and an imported job point in longitude-latitude order. Both numeric values fall within legal global ranges, so a simple bounds check alone misses the swap. The import contract identifies each field name and coordinate system, and the application rejects the unlabeled pair. For J-47, the verified entrance point differs from the building centroid; the route uses the entrance. A manager-facing summary names the service area, while the exact customer location remains in the authorized dispatch tool.",
         sample="Depot: latitude, longitude, declared coordinate system.\nImported J-47 pair: order missing -> reject until mapped.\nJ-47 route target: verified service entrance, not centroid.\nPublic summary: service area only.\nDispatch tool: exact point under access control.",
         cost="Validating N coordinate records is O(N). Detecting swapped-but-in-range values may require contextual checks against known service bounds or a sample review, adding O(N) comparisons. The extra metadata is tiny compared with an incorrect trip. Reduce precision only in outputs where exact location is unnecessary; do not round the operational route input so far that the driver loses the correct entrance.",
         mistakes=["Do not assume coordinate order from unlabeled numbers.", "Do not equate a building centroid with an approved entrance.", "Do not expose exact customer coordinates in a broad status message."],
         related=["prompt-engineering/locale-formatting-structured-values", "prompt-engineering/privacy-and-data-minimization", "prompt-engineering/sensitive-output-redaction-gate"]),
    dict(slug="location-prompt-travel-estimate-provenance-and-freshness", title="Location prompts: label travel estimates and stale matrices", section=applications,
         summary="Keep departure time, mode, and estimate source attached to each route leg.",
         definition="Travel time is an estimate for a particular origin, destination, mode, departure time, and routing preference. A prompt must not present a cached number as current traffic. The application should attach generation time, validity window, distance unit, and any fallback status to every route leg. If an element has no route or the provider used a fallback method, mark it for review rather than inventing a duration. For a multi-stop plan, retrieve the needed pairwise legs and check that all origins and destinations correspond to verified stop identities. The model can explain trade-offs but should not fabricate matrix cells.",
         case="Quartz requests a driving matrix for three verified jobs and depot start at the planned morning departure. The result gives 22 minutes from depot to J-47, 18 minutes from J-47 to J-52, and 31 minutes from J-52 to J-71. A saved matrix from the previous week lists 16 minutes for the last leg; the prompt rejects that older cell for today's plan. If the current J-52 to J-71 element is missing, the route remains provisional even though the other two legs are available.",
         sample="Mode: driving; departure: planned morning instant.\nFresh legs: depot→J-47 22 min; J-47→J-52 18 min.\nFresh leg: J-52→J-71 31 min.\nOld J-52→J-71 value: 16 min -> do not substitute.\nMissing current element -> provisional plan.",
         cost="A complete matrix for S stops can require O(S squared) origin-destination elements, while evaluating one fixed sequence needs only O(S) legs. Request only the combinations required by the planner and retain a matrix ID for review. Refreshing estimates adds network latency and possibly usage cost, but avoids a false on-time claim. A routing service may return estimates with uncertainty; the prompt should preserve that status instead of turning a prediction into a guaranteed arrival.",
         mistakes=["Do not present a week-old leg as current traffic.", "Do not fill a missing matrix cell with an invented time.", "Do not call an estimated arrival a guaranteed arrival."],
         related=["prompt-engineering/retrieval-freshness-and-conflict", "prompt-engineering/time-sensitive-research-contract", "prompt-engineering/architecture-capacity-units-and-headroom-check"]),
    dict(slug="location-prompt-stop-window-feasibility-check", title="Location prompts: compute stop-window feasibility before recommending", section=production,
         summary="Combine travel legs, service durations, and appointment windows with checked arithmetic.",
         definition="A route recommendation must satisfy more than short travel distance. For each stop, compute arrival from the previous departure and the selected travel estimate, then start service no earlier than the appointment window and finish within any hard end constraint. Preserve service duration, skill eligibility, capacity, break rules, and access restrictions as typed inputs. The prompt may rank feasible options, but a deterministic validator should reject routes with a missed hard window or missing leg. If a window is soft, label the trade-off explicitly; do not quietly reinterpret it as hard or vice versa.",
         case="Technician T-8 leaves the Quartz depot at 08:30. A 22-minute leg reaches J-47 at 08:52; service waits until the 09:00 window and lasts 30 minutes, ending 09:30. An 18-minute leg reaches J-52 at 09:48; service starts 10:00 and ends 10:25 after 25 minutes. A 31-minute leg reaches J-71 at 10:56; service starts 11:00 and ends 11:20 after 20 minutes. Those calculations support the three stated windows, but only if the technician is eligible for all jobs and the travel estimates remain valid.",
         sample="T-8 departs 08:30; depot→J-47 22 min; arrives 08:52.\nJ-47 window 09:00; service 30 min; departs 09:30.\nJ-52 arrival 09:48; starts 10:00; departs 10:25.\nJ-71 arrival 10:56; starts 11:00; finishes 11:20.\nRelease gate: skill, capacity, breaks, and access checked.",
         cost="Validating one ordered route of S stops is O(S) time and O(1) working state beyond the input. Searching every permutation is O(S factorial) and quickly impractical; use a route solver or bounded candidate set for larger fleets, then validate the chosen route independently. A few precise arithmetic checks prevent a fluent prompt from hiding a ten-minute conflict. Keep traffic estimates separate from appointment rules so a later refresh changes only the affected legs.",
         mistakes=["Do not add travel time without waiting for a window that has not opened.", "Do not ignore service duration when checking the next stop.", "Do not call a route feasible before skill and capacity rules are checked."],
         related=["prompt-engineering/deterministic-calculation-gates", "prompt-engineering/architecture-capacity-units-and-headroom-check", "prompt-engineering/aggregate-denominator-reconciliation"]),
    dict(slug="location-prompt-route-release-and-map-review", title="Location prompts: review the map and gate dispatch effects", section=production,
         summary="Check rendered stops and require current approval before sending a route.",
         definition="A route can pass arithmetic checks while its map points to the wrong entrance or omits a restricted road. The release packet should include ordered stop IDs, verified point identities, leg estimates, appointment windows, and a rendered map for human review. The map is a view of the route data, not proof that the points were correct. Before dispatching a change, recheck job status and technician availability; a completed or cancelled job must not remain in an active route. Sending the plan to a technician is an external effect with a recipient and receipt. If an update times out, reconcile the dispatch state before retrying.",
         case="Quartz's plan for T-8 passes the three window calculations. The map preview reveals that J-52's marker sits at a loading dock closed to service vehicles, although the street address matches. The dispatcher substitutes the verified service entrance, refreshes affected travel legs, and reruns the feasibility check. Only after reviewing the updated route and the technician recipient does the user approve dispatch. A timeout after send triggers a receipt lookup; the assistant does not issue a second route simply because it cannot see the first response.",
         sample="Review: ordered job IDs, entrance points, windows, leg IDs.\nMap defect: J-52 marker at closed dock -> correct point.\nRefresh changed legs and recompute arrivals.\nBefore send: job status and T-8 availability rechecked.\nSend timeout: query dispatch receipt before retry.",
         cost="A map review adds a fixed human inspection plus O(S) stop checks for S route points. Recomputing only legs adjacent to a corrected stop is cheaper than rebuilding every candidate route, though global optimization may still be warranted if the correction changes feasibility. Receipt checks are O(1) average in a keyed store. The extra gates reduce wrong-address dispatches and duplicate technician instructions, both costlier than a short review.",
         mistakes=["Do not treat a rendered map as validation of the original point identities.", "Do not send a route that still contains a cancelled job.", "Do not resend after an ambiguous dispatch timeout without checking the receipt."],
         related=["prompt-engineering/chart-prompt-accessibility-and-render-review", "prompt-engineering/side-effect-receipt-reconciliation", "prompt-engineering/browser-effect-receipt-and-recovery"]),
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]) & lookup.keys()
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: review a Quartz field-service route"
titles[quiz_path] = "Location-aware prompt decisions"


def link(path):
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(selected):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(selected)) + "</ul>"


def related(selected):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(selected)]


def article(path, title, summary, body, section, order, connections, kind="tutorial"):
    row = copy.deepcopy(lookup["prompt-engineering/evaluation-slice-design"])
    subjects = {applications: "prompt-engineering-applications", production: "prompt-engineering-production", projects: "prompt-engineering-project"}
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path, title=title,
               summary=summary, body=body, subject=subjects[section], difficulty="Advanced",
               tags=["prompt engineering", "location dispatch"], sort_order=31500 + order,
               status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"].update(kind=kind, reading_minutes=11 if kind == "tutorial" else 18,
                       author_path="authors/aitrove-editorial", subject_root=subject_root,
                       section_path=section, content_format="html", seo_ready=True,
                       related=related(connections))
    return row


new_rows = []
for index, (path, spec) in enumerate(zip(paths, specs)):
    connections = [spec["section"], subject_root] + spec["related"] + [other for other in paths if other != path] + [project_path, quiz_path]
    body = ("<p>" + html.escape(spec["definition"]) + "</p>"
            + "<h2>Operational case</h2><p>" + html.escape(spec["case"]) + "</p>"
            + '<pre><code class="language-text">' + html.escape(spec["sample"], quote=False) + "</code></pre>"
            + "<h2>Performance and operating cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
            + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in spec["mistakes"]) + "</ul>"
            + "<h2>Connected lessons</h2>" + links(connections))
    new_rows.append(article(path, spec["title"], spec["summary"], body, spec["section"], index * 10, connections))

project_connections = paths + ["prompt-engineering/deterministic-calculation-gates", "prompt-engineering/chart-prompt-accessibility-and-render-review", quiz_path]
project_body = (
    "<p>Plan a fictional morning route for Quartz Field Service technician T-8. Three jobs have verified service entrances and fixed appointment windows. A fourth address is ambiguous and must remain outside the final candidate until the dispatcher confirms its street number. The task is to prepare a reviewable route recommendation, not to send directions. The prompt must keep address identity, coordinate order, travel estimates, service durations, and dispatch authority separate.</p>"
    "<h2>Validate locations and route inputs</h2><p>For J-47, choose the full street-address match at 47 Harbor Lane after comparing it with a partial match in another district. Reject an imported coordinate pair whose order is not declared. Use the verified service entrance instead of a building centroid. The current driving matrix supplies 22 minutes from depot to J-47, 18 to J-52, and 31 to J-71 for the planned departure. A week-old 16-minute estimate for the last leg is not a substitute. A missing current leg leaves the plan provisional.</p>"
    "<h2>Compute and review</h2><p>T-8 leaves at 08:30, reaches J-47 at 08:52, waits until 09:00, and finishes 30 minutes of service at 09:30. The next leg reaches J-52 at 09:48; its 10:00 start and 25-minute service end at 10:25. The final leg reaches J-71 at 10:56; a start at 11:00 and 20-minute service end at 11:20. Those times satisfy the stated windows only if skills, capacity, access, and break rules also pass. The map preview reveals a closed loading dock at J-52, so the dispatcher corrects the entrance and refreshes affected legs before approval.</p>"
    '<pre><code class="language-text">J-47: 08:52 arrival; 09:00–09:30 service.\nJ-52: 09:48 arrival; 10:00–10:25 service.\nJ-71: 10:56 arrival; 11:00–11:20 service.\nAmbiguous fourth address: excluded.\nJ-52 closed dock: correct point, refresh legs, recompute.\nDispatch: pending current user review and effect receipt.</code></pre>'
    "<h2>Performance and operating cost</h2><p>Validation of one ordered S-stop route is O(S), while a full pairwise travel matrix can grow as O(S squared). Searching every stop ordering grows factorially, so larger fleets need bounded candidates or a dedicated solver followed by independent validation. Map review and permission checks add time but expose errors that arithmetic cannot. The final packet includes place identities, matrix version, computed times, map artifact, recipient, and any dispatch receipt.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not use the partial address match as a verified stop.</li><li>Do not guess coordinate order.</li><li>Do not replace a missing current leg with an old estimate.</li><li>Do not ignore waiting and service durations.</li><li>Do not send an unreconciled route after a timeout.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Check stop identity, current legs, window arithmetic, map points, and dispatch authority.", project_body, projects, 60, project_connections, "project"))

questions = [
    ("How should an ambiguous address enter a final route?", "Only after trusted selection of a verified candidate", "By choosing the first result", "By choosing the nearest street", "A partial match is not a confirmed destination."),
    ("Which J-47 location should the vehicle target?", "The verified service entrance", "Any point inside the building", "A nearby street centroid", "An operational entrance may differ from a building centroid."),
    ("What is wrong with an unlabeled coordinate pair?", "Order and coordinate system are unknown", "It has two numbers", "It is always latitude first", "Range checks alone do not establish field meaning."),
    ("May an old 16-minute leg replace a missing current 31-minute estimate?", "No; mark the plan provisional", "Yes, without disclosure", "Yes, because it is shorter", "Stale and missing estimates cannot be presented as current."),
    ("What metadata belongs with a travel estimate?", "Mode, departure time, origin, destination, and freshness", "Only color", "Only a street name", "The estimate is conditional on its request inputs."),
    ("When does J-47 service start after an 08:52 arrival?", "09:00", "08:52", "09:22", "The appointment window opens at 09:00."),
    ("When does J-52 service finish?", "10:25", "10:07", "09:48", "It starts at 10:00 and lasts 25 minutes."),
    ("When does T-8 arrive at J-71 from J-52?", "10:56", "10:43", "11:31", "10:25 plus 31 minutes is 10:56."),
    ("What else must pass before calling this route feasible?", "Skills, capacity, access, and break rules", "A polished summary", "A shorter map label", "Window arithmetic is only one constraint."),
    ("The map shows J-52 at a closed dock. What follows?", "Correct the point and refresh affected legs", "Send anyway", "Ignore the map", "A correct street address can still have a wrong entrance."),
    ("Does a rendered map prove stop identity?", "No, verify place identities separately", "Yes, every marker is authoritative", "Only when zoomed in", "Rendering reflects the supplied points, including wrong ones."),
    ("A dispatch send times out. What is the next step?", "Check the dispatch receipt before retry", "Send again immediately", "Claim the driver received it", "The first effect may have happened."),
]
quiz = copy.deepcopy(lookup["quizzes/prompt-engineering-email-calendar"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Test address identity, travel freshness, route arithmetic, and dispatch receipts.",
            body="<p>Choose the location-aware decision supported by verified stops and current route data.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, production, quizzes]),
            sort_order=31570, status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"].update(subject_root=subject_root, section_path=quizzes, content_format="html",
                    author_path="authors/aitrove-editorial", seo_ready=True, duration_minutes=12,
                    related=related(paths + [project_path]),
                    questions=[{"prompt": prompt,
                                "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                "answer": (-index) % 3, "explanation": explanation}
                               for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)])
new_rows.append(quiz)

for hub_path, selected, title, summary in [
    (applications, paths[:3], "Location and travel inputs", "Resolve stop identities, coordinates, and current travel estimates."),
    (production, paths[3:], "Route feasibility and release", "Compute windows, inspect map points, and gate dispatch effects."),
    (projects, [project_path], "Quartz dispatch route review", "Apply location and route checks to a three-stop field-service plan."),
    (quizzes, [quiz_path], "Location-aware decisions", "Test address, coordinate, travel, timing, and receipt boundaries."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

lookup[subject_root]["body"] += "<h2>Location-aware dispatch prompts</h2><p>Check addresses, route evidence, feasibility, and release before moving a vehicle.</p>" + links(paths + [project_path, quiz_path])
lookup[subject_root]["updated_at"] = stamp

backlinks = {
    "prompt-engineering/browser-target-grounding-and-stale-state": paths[0],
    "prompt-engineering/locale-formatting-structured-values": paths[1],
    "prompt-engineering/retrieval-freshness-and-conflict": paths[2],
    "prompt-engineering/deterministic-calculation-gates": paths[3],
    "prompt-engineering/chart-prompt-accessibility-and-render-review": paths[4],
    "prompt-engineering/side-effect-receipt-reconciliation": paths[4],
}
for old_path, new_path in backlinks.items():
    entry = lookup[old_path]
    entry["body"] += "<p><strong>Continue with:</strong> " + link(new_path) + ".</p>"
    entry["data"]["related"] = related([item["path"] for item in entry["data"].get("related", [])] + [new_path])
    entry["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newLessons": len(specs), "newProjects": 1, "newQuizzes": 1,
                  "newPaths": [entry["path"] for entry in new_rows]}))
