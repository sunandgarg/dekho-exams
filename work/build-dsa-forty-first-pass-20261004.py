"""Add five independent DSA lessons and connect their audit materials."""

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
subject = "dsa/dsa-tutorial-learn-data-structures-and-algorithms"
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def links(paths):
    return "<ul>" + "".join('<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>" for path in paths) + "</ul>"


lessons = [
    dict(path="dsa/persistent-subarray-kth-order-statistics", program="persistent_kth_shipment_rank.py",
         template="dsa/persistent-segment-tree-versioned-sums", section="dsa/range-query-structures",
         title="Persistent subarray ranks: subtract prefix frequency trees",
         summary="Find the kth smallest value in a frozen subarray using two retained count roots.",
         definition="A persistent order-statistic index keeps one frequency segment-tree root after each prefix of an immutable array. Values are first compressed into sorted ranks. Inserting the next value copies only the nodes on its rank path; all unaffected nodes remain shared with the previous root. A half-open query [l,r) subtracts counts in root l from corresponding counts in root r. At each value split, that difference gives the number of requested elements in the lower-ranked half. Descend left if the requested one-based rank fits there; otherwise subtract that count and descend right. Duplicate values increment a leaf count, so repeated priorities occupy consecutive order positions rather than vanishing as they would in a set. Roots represent insertion history, not editable versions of arbitrary array positions.",
         case="Shipment priorities [47,19,61,29,19,83,37] produce eight roots, including the empty prefix. In [1,6), the sorted priorities are [19,19,29,61,83], so rank three returns 29. Across the complete array, rank six returns 61. In [2,5), rank two is 29. The left root must be subtracted from the right root at every branch; using only the right root silently includes earlier shipments. A request for rank zero, a rank above the interval length, or an empty interval is rejected. This index returns a value, not which duplicate shipment record supplied it.",
         cost="Let N be array length and U the number of distinct values. Sorting and compression cost O(N log N) time. The empty count tree occupies O(U) nodes; N path-copy insertions cost O(N log U) time and new nodes, making total retained space O(U + N log U). Each valid kth query takes O(log U) time and O(1) auxiliary space in the iterative descent. Python node objects carry more memory than packed integer arrays. A static wavelet tree can answer related ranks with another layout; a single sorted copy cannot isolate an arbitrary subarray without extra indexing. Rebuilding is required after changing the source array.",
         mistakes=["Do not forget the left-prefix subtraction at each child.", "Do not discard duplicate values during rank counting.", "Do not use zero-based k with this one-based API.", "Do not mutate a node shared by older prefix roots."],
         related=["dsa/persistent-segment-tree-versioned-sums", "dsa/persistent-range-mex-last-occurrence-index", "dsa/wavelet-tree-subarray-order-statistics", "dsa/wavelet-matrix-static-rank-quantile", "dsa/merge-sort-tree-threshold-count", "dsa/fenwick-order-statistic-multiset"]),
    dict(path="dsa/segment-tree-maximum-subarray-burst", program="max_subarray_fault_bursts.py",
         template="dsa/segment-tree-range-sum-update", section="dsa/range-query-structures",
         title="Maximum-subarray segment trees: preserve the crossing burst",
         summary="Store total, prefix, suffix, and best contiguous sum for range queries and point fixes.",
         definition="A maximum-subarray segment tree summarizes each nonempty interval by four values: its total sum, greatest nonempty prefix sum, greatest nonempty suffix sum, and greatest nonempty contiguous subarray sum. When adjacent summaries join, the best interval is either inside the left child, inside the right child, or crosses their boundary as the left suffix plus the right prefix. The prefix and suffix also account for an entire neighboring child. This four-field join is associative for consecutive intervals, which permits ordinary segment-tree range decomposition. A point replacement rebuilds only its ancestors. The model scores nonempty fault bursts; a zero-length range is invalid, and a wholly negative range returns its least-negative single score rather than zero.",
         case="For fault scores [-8,47,-19,61,-83,29,37], the largest contiguous score over the whole feed is 89 from [47,-19,61]. Within [4,7), the best is 66 from [29,37]. Correcting position four from -83 to -17 changes the whole-feed best to 138, because one longer stretch now crosses the old break. A plain range-sum tree would report totals but could not distinguish the crossing candidate. Returning a zero summary for a non-overlapping query branch would also be wrong: zero would invent an empty subarray in a contract that forbids one.",
         cost="Building all summaries costs O(N) time and space for N scores. A replacement and a nonempty range query each touch O(log N) nodes, with O(1) work per join. Recursive calls use O(log N) stack space. The summary stores sums, not the winning endpoint positions; retaining endpoints requires a tie rule and additional fields. It does not support a constant-time arbitrary range addition: changing every value can change the winning interval in a way four old numbers cannot repair. For one fixed array with no updates, a direct scan may be simpler; repeated bounded queries or corrections justify the index.",
         mistakes=["Do not treat a zero summary as identity when the winning subarray must be nonempty.", "Do not omit the suffix-plus-prefix crossing case.", "Do not call the best total a range sum; it may exclude endpoints.", "Do not assume these four fields support lazy range addition."],
         related=["dsa/segment-tree-range-sum-update", "dsa/lazy-segment-tree-affine-range-sums", "dsa/segment-tree-beats-range-cap-sum", "dsa/cartesian-tree-static-range-minimum", "dsa/disjoint-sparse-table-range-sum", "dsa/square-root-block-range-sum"]),
    dict(path="dsa/li-chao-tree-interval-limited-line-offers", program="li_chao_segment_tariffs.py",
         template="dsa/li-chao-tree-line-minimum", section="dsa/range-query-structures",
         title="Li Chao interval offers: limit each line to its valid minutes",
         summary="Insert an affine price only over its allowed integer interval and ask for the least charge.",
         definition="An interval-limited Li Chao index answers the minimum value among lines that are valid at a queried integer coordinate. Its outer segment recursion decomposes each offer's half-open validity interval into covered nodes. Inside each covered node, a Li Chao insertion keeps the line that is cheaper at that node's midpoint and sends a displaced line toward the side where it can still win. Two distinct affine lines cross at most once, which makes that displacement rule valid. A point query follows the coordinate path and evaluates every stored line it encounters. The example uses one fixed integer minute domain, accepts overlapping offers and negative slopes, and returns no result where no offer covers the minute. Lines remain after insertion; there is no expiration or deletion operation.",
         case="On minutes [0,16), a base offer charges 3x+47 everywhere. A second charges -2x+83 only on [4,12), and a third charges x+29 only on [9,16). The least prices at minutes 2, 7, 10, and 15 are 53, 68, 39, and 44. At minute 7, the second line costs 69, so the base offer wins by one; at minute 10, the third offer costs 39. Evaluating the second line at minute 15 would be a correctness error even if it happened to be cheaper. Query endpoints are integer points and the interval right endpoint is excluded.",
         cost="Let D be the number of integer coordinates in the fixed domain. A validity interval decomposes into O(log D) covered segment nodes, and placing a line inside each can descend O(log D) more levels, so one offer insertion costs O(log squared D) worst-case time. A point query reads O(log D) nodes. The sparse dictionary retains up to O(M log squared D) line-bearing nodes after M offers in the worst case, plus recursion of O(log D). This implementation does not prove a smaller compressed-memory bound. Whole-domain Li Chao insertion is cheaper because it performs only one placement. A linear scan over M active offers costs O(M) per query and can be preferable for a tiny catalog.",
         mistakes=["Do not let a line affect coordinates outside its validity interval.", "Do not compare only slopes; intercepts decide where lines cross.", "Do not query outside the fixed integer domain.", "Do not describe insertion here as the whole-domain O(log D) operation."],
         related=["dsa/li-chao-tree-line-minimum", "dsa/sparse-coordinate-segment-tree", "dsa/segment-tree-interval-stabbing-index", "dsa/segment-tree-range-sum-update", "dsa/disjoint-sparse-table-range-sum", "dsa/lazy-segment-tree-affine-range-sums"]),
    dict(path="dsa/all-one-frequency-bucket-counter", program="frequency_bucket_alerts.py",
         template="dsa/lfu-cache-frequency-and-recency-eviction", section="dsa/hash-tables",
         title="All-one frequency buckets: increment, decrement, and read both extremes",
         summary="Move alert keys between adjacent count buckets and keep minimum and maximum counts at the ends.",
         definition="An all-one counter keeps a doubly linked list of nonempty frequency buckets in increasing count order. Each bucket owns a set of keys at one count, and a hash map points each live key to its bucket. Increment moves a key into the next bucket, creating that adjacent count bucket if absent. Decrement moves it backward or deletes it when its count falls from one to zero. Empty buckets are removed immediately. The first live bucket holds a minimum-count key; the last holds a maximum-count key. The API may return any key when several share an extreme frequency. This is a mutable in-memory count index, not a time-decayed stream estimate or an LFU cache with a tie-breaking eviction policy.",
         case="Record dock-47 three times, dock-19 twice, and dock-61 once. The minimum key is dock-61 and the maximum is dock-47. After decrementing dock-47 twice, both dock-47 and dock-61 are at count one, so either is an acceptable minimum; dock-19 is the unique maximum. Removing dock-61's last count leaves dock-47 as the minimum and dock-19 as the maximum. Decrementing an absent code raises an error instead of creating a negative count. When the index is empty, both endpoint reads return no key.",
         cost="Every operation touches one hash-map entry, at most two neighboring buckets, and constant-time set insertions or removals under usual hash-table assumptions. Increment, decrement, minimum, and maximum are therefore O(1) expected time, with O(K) space for K live keys and at most K nonempty buckets. Adversarial hash collisions can defeat that expected bound in a general hash table. Python set iteration chooses an arbitrary tied key and offers no stable ordering promise. A heap-based count index must manage stale priorities after each count change; linked adjacent buckets avoid stale records because a single update changes frequency by exactly one.",
         mistakes=["Do not retain an empty frequency bucket between its neighbors.", "Do not assume an arbitrary tied key is the oldest or lexicographically smallest.", "Do not decrement an absent key into a negative count.", "Do not claim worst-case O(1) hashing under adversarial collisions."],
         related=["dsa/lfu-cache-frequency-and-recency-eviction", "dsa/space-saving-topk-stream-summary", "dsa/misra-gries-frequent-item-candidates", "dsa/hash-map-collision-and-load-contract", "dsa/ttl-heap-expiration-with-stale-records", "dsa/dual-heap-double-ended-priority-queue"]),
    dict(path="dsa/patricia-binary-prefix-routing-index", program="patricia_prefix_routes.py",
         template="dsa/binary-radix-longest-prefix-routes", section="dsa/trees-and-heaps",
         title="Patricia binary routing: compress chains without losing prefix matches",
         summary="Split compressed binary edges when a shorter network or diverging route arrives.",
         definition="A Patricia-style binary routing trie stores only branching and route-bearing prefixes rather than one node for every address bit. Each node holds the full bit prefix it represents, an optional destination, and up to two children keyed by the next bit. Insertion compares a new network prefix against a child edge and splits that edge at the first differing bit or where the new prefix ends. A lookup follows only edges whose complete compressed span matches the address, retaining the last destination seen. That last stored route is the longest matching prefix. Prefix bits are compared, not just numeric network values, because two routes with the same initial bits may diverge within a compressed edge. This example fixes addresses at eight bits and supports insertion and destination replacement, not deletion or address-family expansion.",
         case="Insert a default route, then prefixes 176/5 and 184/5, followed by their shorter regional ancestor 160/3. The late ancestor insertion splits an existing compressed path and preserves both longer routes. Address 178 selects north-depot, 190 selects south-depot, 171 selects regional-gateway, and 132 falls through to default-gateway. Replacing 176/5 with north-backup changes only addresses with that longest match. The actual prefix represented by 176/5 is its first five bits, so low bits of the network argument do not identify a separate route at that prefix length.",
         cost="With width W bits, insertion and lookup compare at most W bit positions across the traversed compressed edges, taking O(W) time in this string-based model. A newly inserted route adds at most one leaf and one split node; stored full-prefix strings can cost O(PW) total characters for P routes, while the node count is O(P). A full binary radix trie may spend a node per traversed bit and can be simpler to update. Here compression helps sparse routing tables but does not provide deletion, concurrent publication, or a real packet-forwarding benchmark. The eight-bit example is a correctness model, not a network stack.",
         mistakes=["Do not match a child after only its first branch bit; check its whole compressed span.", "Do not overwrite a longer route when inserting a shorter ancestor.", "Do not return the deepest visited node unless it actually stores a destination.", "Do not treat an eight-bit demonstration as an IPv4 or IPv6 implementation."],
         related=["dsa/binary-radix-longest-prefix-routes", "dsa/binary-trie-maximum-xor-multiset", "dsa/compressed-trie-edge-splitting", "dsa/adaptive-radix-node-fanout-incident-codes", "dsa/double-array-trie-static-incident-codes", "dsa/louds-level-order-alert-trie"]),
]

for number, lesson in enumerate(lessons):
    path = lesson["path"]
    assert path not in by_path
    program = (root / "work/dsa-programs" / lesson["program"]).read_text().rstrip()
    output = subprocess.run([sys.executable, "-c", program], capture_output=True, text=True, check=True).stdout.strip()
    related = [lesson["section"], subject, *lesson["related"], "dsa/projects", "dsa/quizzes"]
    body = "<p>" + html.escape(lesson["definition"]) + "</p>"
    body += "<h2>Operational case</h2><p>" + html.escape(lesson["case"]) + "</p>"
    body += '<h2>Working Python program</h2><pre><code class="language-python">' + html.escape(program, quote=False) + "</code></pre>"
    body += '<h3>Output</h3><pre><code class="language-text">' + html.escape(output) + "</code></pre>"
    body += "<h2>Time, space, and tradeoff</h2><p>" + html.escape(lesson["cost"]) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in lesson["mistakes"]) + "</ul>"
    body += "<h2>Connected lessons</h2>" + links(related)
    entry = copy.deepcopy(by_path[lesson["template"]])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path, title=lesson["title"],
                 summary=lesson["summary"], body=body, sort_order=48000 + 10 * number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"].update(section_path=lesson["section"],
                         related=[{"path": target, "title": by_path[target]["title"]} for target in related])
    entries.append(entry)
    by_path[path] = entry
    for hub_path in (lesson["section"], subject):
        hub = by_path[hub_path]
        module = hub["data"]["modules"][0] if hub_path == lesson["section"] else next(
            module for module in hub["data"]["modules"] if module["title"] == by_path[lesson["section"]]["title"])
        module["lessons"].append(path)
        hub["body"] += '<p><a href="/' + path + '">' + html.escape(lesson["title"]) + "</a></p>"
        hub["updated_at"] = stamp

paths = [lesson["path"] for lesson in lessons]
project_path = "dsa/rank-burst-tariff-frequency-routing-audit-project"
quiz_path = "quizzes/dsa-rank-burst-tariff-frequency-routing-contracts"
project = copy.deepcopy(by_path["dsa/range-mex-xor-affine-priority-audit-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: audit ranks, bursts, tariffs, count extremes, and routes",
               summary="Check five indexes against direct sorted, scanned, and prefix-match models.",
               sort_order=48060, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=40,
                       related=[{"path": path, "title": by_path[path]["title"]} for path in paths])
project["body"] = "<p>A dispatch console has five different lookup contracts. A historical shipment interval needs its kth priority; a fault-score interval needs its best contiguous burst after corrections; a tariff applies only during certain minutes; an alert counter needs keys at both frequency extremes; and an address needs its longest valid route prefix. Implement these as separate indexes, because each stores different invariants and accepts different mutations. The first array is frozen, the burst tree permits point replacement, the tariff index adds interval-limited lines, the counter increments or decrements keys by one, and the compressed route trie inserts or replaces destinations.</p>"
project["body"] += "<h2>Acceptance trace</h2><p>For priorities [47,19,61,29,19,83,37], rank three in [1,6) is 29. For fault scores [-8,47,-19,61,-83,29,37], the best nonempty burst is 89; replacing -83 with -17 makes it 138. For the three tariff offers in the working program, minute ten costs 39 and minute fifteen costs 44. For the alert stream, dock-61 starts as the unique minimum-count key and dock-47 as the unique maximum. For the routing table, addresses 178, 190, 171, and 132 choose north, south, regional, and default destinations. Keep these values as independent acceptance checks, not as data copied between structures.</p>"
project["body"] += "<h2>Failure and cost review</h2><p>Enumerate sorted subarrays, nonempty contiguous sums, active tariff lines, direct key counts, and matching route prefixes for small inputs. Reject an empty kth interval and an invalid rank; keep duplicate priorities. Test an all-negative burst and a correction at either endpoint. Query a minute with no active tariff to confirm the no-result path, and confirm an offer's right endpoint is excluded. Mix count increments with decrements through bucket removal, allowing any tied extreme key. Insert a short route after longer descendants so the compressed edge must split without losing them. Report each structure's separate construction, query, update, and storage cost.</p>"
project["body"] += "<h3>Common Mistakes</h3><ul><li>Do not count values outside the requested prefix-root difference.</li><li>Do not let an empty burst win a nonempty query.</li><li>Do not evaluate a tariff outside its valid minutes.</li><li>Do not assign stable order to tied frequency keys.</li><li>Do not stop route matching after checking only one bit of a compressed edge.</li></ul>"
project["body"] += "<h2>Connected lessons</h2>" + links(paths + ["dsa/projects", "dsa/quizzes", subject])
entries.append(project)
by_path[project_path] = project

raw = [
    ("Which two roots define the frequency multiset for [l,r)?", "Subtract root l from root r", "Add root l to root r", "Use root r without subtraction", "Each root counts a whole prefix; their difference leaves exactly the values inserted at positions l through r minus one."),
    ("What does a duplicated value do in a persistent kth index?", "It increments one compressed-rank count", "It is ignored as a set duplicate", "It creates a new distinct rank", "The value catalog stores one coordinate for duplicates, while the leaf count records every occurrence in the requested range."),
    ("What must a maximum-subarray join consider across child intervals?", "The left suffix plus the right prefix", "Only the larger child total", "A zero-length interval at the boundary", "A winning contiguous interval can cross the child boundary only by taking a suffix of the left and a prefix of the right."),
    ("What does an all-negative nonempty burst query return?", "The least-negative element", "Zero from an empty burst", "The sum of every element", "The contract requires at least one score, so the best single negative value remains a valid answer and zero does not."),
    ("How is an interval-limited line inserted?", "Decompose its valid interval, then place the line in covered nodes", "Place it at the root for every minute", "Store only its slope", "Only nodes wholly covered by the offer's allowed minutes may retain the line, while Li Chao placement resolves competing values within each node."),
    ("What should a tariff query return when no offer covers its minute?", "No result", "Zero charge", "The newest offer regardless of interval", "An uncovered minute has no eligible affine line, so the index returns no result rather than inventing a free offer."),
    ("What happens when a frequency bucket becomes empty?", "Unlink it from its neighbors", "Leave it as the minimum forever", "Copy all keys into the next bucket", "Keeping only nonempty buckets makes the head and tail neighbors identify actual minimum and maximum live counts."),
    ("Which tied key must a frequency endpoint return?", "Any key in the extreme-count bucket", "The oldest inserted key", "The lexicographically smallest key", "The bucket stores an unordered set and the contract specifies count extremes, not a stable order among equal counts."),
    ("Why can one frequency increment move locally?", "Its count changes by exactly one", "Counts are sorted by key name", "All buckets are rebuilt each call", "An increment changes a key's count from c to c plus one, so its target bucket can only be the next adjacent count bucket."),
    ("What must a compressed route lookup check before descending?", "Every skipped bit along that child prefix", "Only the first branching bit", "The destination string alphabetically", "A compressed child represents a complete bit span; a first-bit match alone may hide a later mismatch on that same edge."),
    ("Which route wins after several stored prefixes match an address?", "The longest matching stored prefix", "The first inserted route", "The route with the lowest network value", "Retaining the last destination reached along a fully matched prefix path gives the most specific applicable route."),
    ("What happens when a shorter route arrives inside an existing compressed edge?", "Split the edge and keep its longer descendant", "Overwrite and discard the longer route", "Reject every shorter route", "The shorter prefix becomes a route-bearing split node while the existing longer child remains attached below the appropriate next bit."),
]
questions = []
for number, (prompt, correct, wrong_one, wrong_two, explanation) in enumerate(raw):
    assert len(explanation) >= 60
    answer = number % 3
    options = [wrong_one, wrong_two]
    options.insert(answer, correct)
    questions.append({"prompt": prompt, "options": options, "answer": answer, "explanation": explanation})
quiz = copy.deepcopy(by_path["quizzes/dsa-range-mex-xor-affine-priority-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Check persistent ranks, fault bursts, tariff offers, counts, and routes",
            summary="Twelve explained decisions about five independent indexing contracts.",
            sort_order=48070, created_at=stamp, updated_at=stamp)
quiz["data"].update(duration_minutes=20,
                    related=[{"path": path, "title": by_path[path]["title"]} for path in paths + [project_path]],
                    questions=questions)
quiz["body"] = "<p>Check each structure's retained state, operation boundary, and failure rule against its runnable trace. Several answers depend on an interval endpoint or a count tie.</p><h2>Lessons</h2>" + links(paths) + "<h2>Design exercise</h2>" + links([project_path, subject])
entries.append(quiz)
by_path[quiz_path] = quiz

for hub_path, destination in (("dsa/projects", project_path), ("dsa/quizzes", quiz_path)):
    hub = by_path[hub_path]
    hub["data"]["modules"][0]["lessons"].append(destination)
    hub["body"] += '<p><a href="/' + destination + '">' + html.escape(by_path[destination]["title"]) + "</a></p>"
    hub["updated_at"] = stamp
    root_module = next(module for module in by_path[subject]["data"]["modules"] if module["title"] == hub["title"])
    root_module["lessons"].append(destination)
    by_path[subject]["body"] += '<p><a href="/' + destination + '">' + html.escape(by_path[destination]["title"]) + "</a></p>"
    by_path[subject]["updated_at"] = stamp

for path in paths:
    entry = by_path[path]
    peers = [other for other in paths if other != path]
    entry["body"] += "<p>Compare this operation boundary with " + ", ".join(
        '<a href="/' + other + '">' + html.escape(by_path[other]["title"]) + "</a>" for other in peers)
    entry["body"] += ', then complete the <a href="/' + project_path + '">audit project</a> and <a href="/' + quiz_path + '">decision quiz</a>.</p>'
    entry["updated_at"] = stamp

for lesson in lessons:
    for old_path in lesson["related"][:2]:
        old = by_path[old_path]
        old["body"] += '<p><a href="/' + lesson["path"] + '">' + html.escape(lesson["title"]) + "</a> examines a related structure with a different operation boundary.</p>"
        old["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": 5, "projects": 1, "quizzes": 1, "new_routes": 7}))
