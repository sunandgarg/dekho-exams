"""Add mutable and static spatial indexing structure lessons."""

import copy
import datetime
import html
import json
import subprocess
import sys
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
by_path = {entry["path"]: entry for entry in entries}
subject_root = "dsa/dsa-tutorial-learn-data-structures-and-algorithms"
stamp = datetime.datetime.now(datetime.UTC).isoformat()

lessons = [
    dict(path="dsa/spatial-hash-grid-moving-points", program="spatial_hash_moving_depots.py",
         template="dsa/hash-map-collision-and-load-contract", section="dsa/hash-tables",
         title="Spatial hash grids: move points between occupied cells",
         summary="Index moving coordinates by grid cell and verify distance after candidate lookup.",
         definition="A spatial hash grid maps a coordinate to a cell key, then stores the IDs in that cell. A second map stores each ID's current coordinates so a move can remove it from its previous cell before insertion into the new one. This example uses floor division, including for negative coordinates, and deletes an empty cell after its last point moves or leaves. A radius query enumerates cells touched by the bounding square and checks actual squared distance for every candidate. The cell lookup is a coarse filter. It cannot by itself establish that a point is inside a circle. IDs are unique, and upsert replaces the current position of an existing ID. Coordinates and radius use the same planar units; this is not a latitude-longitude distance calculator.",
         case="Pump-47 starts at minus three, four; valve-19 moves from nine, five to one, six; sensor-61 stays at two, seven. A radius-four query around zero, five returns all three after the move. If the old valve cell retained its ID, a later query there could return a stale location or duplicate result. The implementation computes distance from the authoritative coordinate map rather than trusting which grid cell supplied a candidate. Queries that cross the zero axis still enumerate negative cell numbers correctly because floor division places minus one in the preceding cell rather than truncating it toward zero.",
         cost="An upsert or removal uses expected O(1) hash-map and set work. A query touching C cells and inspecting K candidate points costs O(C + K + R log R) here, where R results are sorted before return. Memory is O(N + E) for N points and E occupied cells. A huge radius or a very small cell size can make C large even when most cells are empty; a hot cell can make K approach N. Hash operations are expected costs, not hard bounds. The index is mutable and single-process but does not support rectangle geometry, geographic projections, or concurrent move/query snapshots.",
         mistakes=["Do not keep an ID in its old cell after a move.", "Do not truncate negative coordinates toward zero when choosing a cell.", "Do not return every point from a touched cell without distance verification.", "Do not describe a large-radius query as constant time."],
         related=["dsa/hash-map-collision-and-load-contract", "dsa/kd-tree-exact-nearest-depot", "dsa/packed-r-tree-rectangle-intersection"]),
    dict(path="dsa/point-region-quadtree-range-report", program="point_region_quadtree_depots.py",
         template="dsa/kd-tree-exact-nearest-depot", section="dsa/trees-and-heaps",
         title="Point-region quadtrees: subdivide crowded cells",
         summary="Split a fixed square into four children and prune nonintersecting query regions.",
         definition="A point-region quadtree recursively divides a fixed square into four equal regions when a leaf holds more than its target capacity. Each point belongs to exactly one child, with midpoint coordinates going to the right or upper child. This implementation uses integer coordinates in a half-open square and half-open query windows. The domain width is a power of two. Subdivision stops at one-cell width or a configured depth, so many points at one coordinate can remain in a crowded leaf instead of causing infinite splitting. Queries traverse only nodes whose regions intersect the requested window and verify each reported point against the exact bounds. Duplicate IDs and out-of-domain inserts are rejected.",
         case="A warehouse map contains pump-47 at 47,52, valve-19 at 19,61, sensor-61 at 52,58, and grid-83 far away at 180,70. A window spanning x from 15 through values below 60 and y from 45 through values below 65 returns the first three. The upper boundary itself is excluded; a point at x 60 belongs outside this request. With capacity two, the first crowded leaf subdivides. A cluster of identical points can still force a deeper path until the configured stop condition, making a bounded leaf size a target rather than an unconditional guarantee.",
         cost="For tree depth D, insertion visits O(D) regions and may redistribute points when a leaf splits; a split can cost the current leaf population, and clustered inputs can reach O(ND) total insertion work. A query costs O(V + K + R log R) for V visited nodes, K points examined in intersecting leaves, and R sorted results. In the worst case V and K scale with N. Space is O(N + V) including point records and allocated children. This fixed-domain tree has no removal, merge-on-delete, automatic domain expansion, or nearest-neighbor API. A grid is simpler when updates dominate and a useful cell size is known.",
         mistakes=["Do not send a midpoint point to two children.", "Do not mix inclusive and half-open rectangle boundaries.", "Do not keep subdividing identical points without a depth or cell-width stop.", "Do not claim every quadtree query visits logarithmically many nodes."],
         related=["dsa/spatial-hash-grid-moving-points", "dsa/kd-tree-exact-nearest-depot", "dsa/packed-r-tree-rectangle-intersection"]),
    dict(path="dsa/static-bvh-axis-aligned-box-overlap", program="static_bvh_depot_boxes.py",
         template="dsa/packed-r-tree-rectangle-intersection", section="dsa/trees-and-heaps",
         title="Bounding-volume hierarchies: prune box overlap searches",
         summary="Build a static binary tree of enclosing rectangles and verify leaf-level intersections.",
         definition="A bounding-volume hierarchy groups geometric objects under enclosing boxes. A query can reject a whole subtree when its enclosure does not intersect the requested box. This program stores axis-aligned rectangles and chooses a binary split by the wider axis of the current enclosure, sorting objects by center along that axis. Each internal node encloses both children; leaves store at most a configured number of original rectangles. Intersections include touching boundaries. The leaf check is necessary because overlapping a parent enclosure only makes its objects candidates. The hierarchy is built once from validated rectangles and is not updated in place. Duplicate IDs and inverted boxes are rejected before construction.",
         case="Pump-47 and valve-19 have partly overlapping service boxes, sensor-61 touches a query near the right edge, and grid-83 lies well outside it. A query box from 40,40 to 75,55 returns the first three after leaf checks. The distant grid subtree may be pruned by its enclosure. If every object is a long rectangle overlapping the same central region, most enclosures overlap the query and the tree can do little pruning. Sorting by center is a deterministic split heuristic, not a guarantee of low overlap or the optimal tree for every workload.",
         cost="At each balanced build level, sorting a subset costs O(M log M), giving O(N log-squared N) time for this direct recursive implementation and O(N) stored nodes and records. Query work is O(V + K + R log R), where V visited nodes, K leaf rectangles tested, and R results sorted; worst-case traversal is O(N). Each intersection check uses constant work on four coordinates. This static index lacks deletion, incremental insertion, and box refitting after movement. For frequently moving objects, rebuild cost may dominate; compare with the moving-point grid and the existing packed R-tree before selecting a representation.",
         mistakes=["Do not report all objects merely because a parent enclosure overlaps.", "Do not use point membership when the stored objects are rectangles.", "Do not claim the center split guarantees small overlap.", "Do not mutate an indexed rectangle without rebuilding or refitting ancestors."],
         related=["dsa/packed-r-tree-rectangle-intersection", "dsa/interval-tree-max-endpoint-pruning", "dsa/spatial-hash-grid-moving-points"]),
    dict(path="dsa/morton-code-ordered-grid-range-index", program="morton_grid_depot_index.py",
         template="dsa/kd-tree-exact-nearest-depot", section="dsa/trees-and-heaps",
         title="Morton ordering: decompose a grid window into code ranges",
         summary="Interleave integer coordinate bits and scan only sorted code intervals for covered cells.",
         definition="A Morton code interleaves bits from x and y to order points in a fixed integer grid. It turns each aligned square cell into one contiguous code interval, but an arbitrary rectangle generally needs many intervals. This static index sorts point records by code. A range query recursively visits aligned square cells; it skips cells outside the half-open rectangle and uses binary search to read the interval for every fully covered cell. Descending partial cells continues until they are inside, outside, or one grid unit wide. Multiple IDs at the same coordinate share a code and are all retained. The method reports exact rectangle membership here because it only scans fully covered cells, not because nearby planar points always receive adjacent codes.",
         case="The same four integer depot points used in the quadtree example are sorted by their interleaved eight-bit coordinates. Querying x from 15 through values below 60 and y from 45 through values below 65 returns pump-47, valve-19, and sensor-61. The grid-83 point is outside. A thin diagonal or narrow rectangle may require many small cell intervals even if few points are returned, so this method should not be advertised as one binary search for every rectangle. It is especially useful as an explanation of how a multidimensional window becomes several one-dimensional runs.",
         cost="Building N records with B bits per coordinate takes O(NB + N log N) time and O(N) stored records and codes. A query costs O(C log N + R log R), where C fully covered cells in the decomposition and R reported points; recursive boundary visits add work proportional to the visited grid cells. C can grow with grid resolution and rectangle shape. The fixed domain is zero through 2^B minus one per coordinate; inserts after construction require rebuilding this immutable list. This implementation supports only exact integer-grid windows and no proximity or geographic-distance guarantee. Morton order preserves some locality but does not preserve all two-dimensional neighbor relations.",
         mistakes=["Do not assume an arbitrary rectangle maps to one Morton interval.", "Do not discard points that share one code.", "Do not treat code proximity as proof of geometric proximity.", "Do not insert outside the configured integer domain without rebuilding the index."],
         related=["dsa/point-region-quadtree-range-report", "dsa/kd-tree-exact-nearest-depot", "dsa/coordinate-compression-ordered-ranks"]),
]


def links(paths):
    return "<ul>" + "".join('<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>" for path in paths) + "</ul>"


for order, lesson in enumerate(lessons):
    path = lesson["path"]
    assert path not in by_path
    source = root / "work/dsa-programs" / lesson["program"]
    program = source.read_text().rstrip()
    output = subprocess.run([sys.executable, str(source)], check=True, capture_output=True, text=True).stdout.strip()
    section = lesson["section"]
    related = [section, subject_root, *lesson["related"], "dsa/projects", "dsa/quizzes"]
    body = (
        "<p>" + html.escape(lesson["definition"]) + "</p>"
        + "<h2>Operational case</h2><p>" + html.escape(lesson["case"]) + "</p>"
        + '<h2>Working Python program</h2><pre><code class="language-python">' + html.escape(program, quote=False) + "</code></pre>"
        + '<h3>Output</h3><pre><code class="language-text">' + html.escape(output) + "</code></pre>"
        + "<h2>Time, space, and tradeoff</h2><p>" + html.escape(lesson["cost"]) + "</p>"
        + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in lesson["mistakes"]) + "</ul>"
        + "<h2>Connected lessons</h2>" + links(related)
    )
    entry = copy.deepcopy(by_path[lesson["template"]])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path, title=lesson["title"], summary=lesson["summary"], body=body,
                 sort_order=42900 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"].update(section_path=section, related=[{"path": target, "title": by_path[target]["title"]} for target in related])
    entries.append(entry)
    by_path[path] = entry
    for hub_path in (section, subject_root):
        hub = by_path[hub_path]
        module = hub["data"]["modules"][0] if hub_path == section else next(module for module in hub["data"]["modules"] if module["title"] == by_path[section]["title"])
        module["lessons"].append(path)
        hub["body"] += '<p><a href="/' + path + '">' + html.escape(lesson["title"]) + "</a></p>"
        hub["updated_at"] = stamp

new_paths = [lesson["path"] for lesson in lessons]
project_path = "dsa/spatial-update-window-overlap-audit-project"
quiz_path = "quizzes/dsa-spatial-grid-tree-code-contracts"
assert project_path not in by_path and quiz_path not in by_path
project = copy.deepcopy(by_path["dsa/priority-queue-meld-monotone-extreme-audit-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: audit moving points and static spatial boxes", summary="Compare grid moves, quadtree windows, box overlap, and Morton code ranges.",
               sort_order=42940, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=30, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths])
project["body"] = (
    "<p>A depot dashboard combines moving vehicle points, fixed facility points, and service rectangles. One index cannot answer every query with the same update cost. Keep an exact dictionary of moving coordinates, an exact list of static points, and an exact list of service boxes in the test program. Compare spatial-hash radius answers after each move, quadtree and Morton window answers against half-open rectangle scans, and bounding-volume overlap answers against closed-box scans. State the coordinate model before testing. These examples use a planar grid; treating degrees of latitude as planar distance would turn an otherwise correct index into a wrong application result.</p>"
    "<h2>Acceptance trace</h2><p>Move valve-19 from nine, five to one, six in a cell-size-eight moving grid and query radius four around zero, five. Insert fixed facilities at 47,52; 19,61; 52,58; and 180,70. A half-open window from x 15 to 60 and y 45 to 65 should return the first three from both quadtree and Morton index. Build four service boxes, then query closed box 40,40 through 75,55; the bounding hierarchy should return the three boxes that overlap, including a boundary touch. Confirm that an absent or inverted query fails according to each API rather than silently changing its geometry.</p>"
    '<h3>Expected review record</h3><pre><code class="language-text">moving-near=[pump-47, sensor-61, valve-19]\nstatic-window=[pump-47, sensor-61, valve-19]\nbox-overlap=[pump-47, sensor-61, valve-19]</code></pre>'
    "<h2>Boundary and cost review</h2><p>Probe negative grid coordinates, moves across cell boundaries, identical quadtree coordinates, points on half-open edges, tiny and empty windows, boxes touching only at one edge, and many boxes whose enclosures overlap the same query. For Morton order, count how many square-code intervals a thin window creates. Compare query candidates with exact outputs after every randomized operation. Explain why a moving-point hash grid pays for enumerated cells, why a fixed-domain quadtree can crowd at its depth limit, why a static bounding hierarchy needs rebuild or refit after movement, and why Morton code sorting alone does not make every geometric query one contiguous range.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not leave moved points in old hash cells.</li><li>Do not mix half-open point windows with closed box intersection.</li><li>Do not report a BVH parent hit without a leaf test.</li><li>Do not collapse every Morton rectangle to one code interval.</li></ul>"
    "<h2>Connected lessons</h2>" + links(new_paths + ["dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("What must a moving-point grid do when an ID changes cells?", ["Remove it from the old cell and add it to the new cell", "Leave it in both cells", "Rebuild every point in the domain"], "The exact ID-to-position map identifies the previous cell so a move cannot leave a stale candidate behind."),
    ("Why check distance after enumerating nearby grid cells?", ["A touched square cell can contain points outside the query circle", "Every touched cell lies wholly inside the circle", "The cell key stores exact radial distance"], "The grid supplies candidates from a bounding square; squared-distance verification enforces the circular query."),
    ("How are negative coordinates mapped to grid cells?", ["By floor division using the configured cell size", "By truncation toward zero", "By taking absolute values first"], "Floor division places coordinates just below zero in the preceding negative cell and keeps cell boundaries consistent."),
    ("Which quadtree child receives a point exactly on a midpoint?", ["The right or upper child for that axis", "Both adjacent children", "Neither child"], "A single tie rule at the midpoint preserves exactly one owning child for every point."),
    ("Why can a quadtree leaf exceed its target capacity?", ["Depth or one-cell width can stop further splitting", "The query deletes old points", "Every internal node keeps all points"], "A finite depth or indivisible grid cell prevents endless subdivision when many points share coordinates."),
    ("What does a half-open window exclude?", ["Points exactly at its right or upper boundary", "Points at its left and lower boundaries", "All points at integer coordinates"], "The range tests left less than or equal to x below right and bottom less than or equal to y below top."),
    ("What allows a bounding hierarchy to prune a subtree?", ["Its enclosing box does not overlap the query box", "One leaf happens to have a different ID", "Its children are stored in sorted order"], "An enclosure disjoint from the query proves every object beneath it is disjoint as well."),
    ("Why test individual boxes at a BVH leaf?", ["A parent enclosure may overlap even when a contained box does not", "The parent contains only exact query matches", "Bounding boxes cannot overlap each other"], "An internal enclosure is a coarse candidate filter; leaf-level geometry decides which original rectangles actually intersect."),
    ("What happens when stored boxes move in this BVH version?", ["The static hierarchy must be rebuilt or separately refitted", "The old enclosures update themselves", "Only the query box needs to change"], "The example constructs enclosures once and provides no incremental path for repairing ancestor bounds after movement."),
    ("What shape maps to one contiguous Morton interval?", ["An aligned square cell in the recursive grid", "Every arbitrary rectangle", "Every circle of fixed radius"], "Interleaved coordinate prefixes define aligned square cells; an arbitrary rectangle usually decomposes into several such intervals."),
    ("Why can two depot IDs share one Morton code?", ["They occupy the same integer-grid coordinate", "The index deletes duplicate coordinates", "The code is a string hash with random collisions"], "A Morton code is determined by coordinates, so distinct IDs at one position produce equal codes and both records must remain."),
    ("What is required for this Morton index after a new point arrives?", ["Rebuild or maintain the sorted code list with a separate update design", "Append blindly and keep binary search correct", "Change the point's ID until its code sorts last"], "The lesson's records and code array are immutable sorted snapshots; an unsorted append breaks interval binary searches."),
]
balanced = []
for number, (prompt, options, explanation) in enumerate(questions):
    distractors = options[1:]
    position = number % 3
    distractors.insert(position, options[0])
    balanced.append({"prompt": prompt, "options": distractors, "answer": position, "explanation": explanation})
quiz = copy.deepcopy(by_path["quizzes/dsa-priority-queue-meld-monotone-extreme-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Spatial grids, quadtrees, boxes, and code ranges", summary="Check moving-cell ownership, region boundaries, box pruning, and Morton intervals.",
            sort_order=42950, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"].update(duration_minutes=20, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths + [project_path]], questions=balanced)
quiz["body"] = "<p>Check the coordinate boundary and update contract before selecting a spatial index. Candidate cells and parent enclosures still require exact result tests.</p><h2>Lessons</h2>" + links(new_paths) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
entries.append(quiz)
by_path[quiz_path] = quiz

for hub_path, destination in (("dsa/projects", project_path), ("dsa/quizzes", quiz_path)):
    hub = by_path[hub_path]
    hub["data"]["modules"][0]["lessons"].append(destination)
    hub["body"] += '<p><a href="/' + destination + '">' + html.escape(by_path[destination]["title"]) + "</a></p>"
    hub["updated_at"] = stamp
    root_module = next(module for module in by_path[subject_root]["data"]["modules"] if module["title"] == hub["title"])
    root_module["lessons"].append(destination)
    by_path[subject_root]["body"] += '<p><a href="/' + destination + '">' + html.escape(by_path[destination]["title"]) + "</a></p>"
    by_path[subject_root]["updated_at"] = stamp

for old_path, new_path in (
    ("dsa/hash-map-collision-and-load-contract", new_paths[0]),
    ("dsa/kd-tree-exact-nearest-depot", new_paths[0]),
    ("dsa/kd-tree-exact-nearest-depot", new_paths[1]),
    ("dsa/kd-tree-exact-nearest-depot", new_paths[3]),
    ("dsa/packed-r-tree-rectangle-intersection", new_paths[2]),
    ("dsa/interval-tree-max-endpoint-pruning", new_paths[2]),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> adds another spatial query contract.</p>"
    old["updated_at"] = stamp
for path in new_paths:
    entry = by_path[path]
    peers = [other for other in new_paths if other != path]
    entry["body"] += '<p>Compare its geometry and update costs with ' + ", ".join('<a href="/' + other + '">' + html.escape(by_path[other]["title"]) + "</a>" for other in peers) + ', then run the <a href="/' + project_path + '">spatial audit</a> and <a href="/' + quiz_path + '">contract quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": new_paths, "project": project_path, "quiz": quiz_path, "questions": len(questions)}))
