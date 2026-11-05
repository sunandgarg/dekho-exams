"""Add checked Java DSA problems and a separate conditional-write Spring lesson."""
from __future__ import annotations

import datetime
import html
import json
import pathlib
import re
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILE = ROOT / "src/data/fixtures.json"
rows = json.loads(FILE.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
added = []


def para(value: str) -> str:
    return "<p>" + re.sub(r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda found: '<a href="/' + found[1] + '">' + found[2] + "</a>", html.escape(value)) + "</p>"


def code(value: str, language: str = "java") -> str:
    return '<pre><code class="language-' + language + '">' + html.escape(value.strip(), quote=False) + "</code></pre>"


def put(slug, title, definition, sections, source, output, cost, mistakes, related, *, spring=False, proof=""):
    path = ("spring/" if spring else "java/") + slug
    assert path not in by_path, path
    assert all(target in by_path for target in related), (path, related)
    subject = "spring-web" if spring else "java-dsa"
    hub = next(row for row in rows if row["type"] == "subject" and row["subject"] == subject)
    body = para(definition)
    for heading, parts in sections:
        body += "<h2>" + html.escape(heading) + "</h2>" + "".join(para(part) for part in parts)
    body += "<h2>" + ("Checked source" if spring else "Working program") + "</h2>" + code(source)
    if spring:
        body += "<h2>Verification boundary</h2>" + para(proof + " runs in the downloadable Spring source kit. The excerpt omits imports and setup; the kit has complete test source.")
    else:
        body += "<h3>Output</h3>" + code(output, "text")
    body += "<h2>Costs and boundaries</h2>" + para(cost)
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in mistakes) + "</ul>"
    body += "<h2>Read next</h2>" + para(", ".join("[[" + target + "|" + by_path[target]["title"] + "]]" for target in related) + ".")
    row = by_path["java/casts"].copy()
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), type="article",
        path=path, title=title, summary=definition, body=body,
        category="Backend Frameworks" if spring else "Programming", subject=subject,
        difficulty="Intermediate", tags=["spring", "spring-boot", slug] if spring else ["java", "dsa", slug],
        status="published", featured=False, sort_order=820 + len(added),
        published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "spring/spring-boot" if spring else "java/java", "section_path": hub["path"],
        "kind": "tutorial", "content_format": "html", "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial", "seo_ready": True,
        "related": [{"path": target, "title": by_path[target]["title"]} for target in related]}
    if spring:
        row["data"].update(framework_version="Spring Boot 4.0.8 / Spring Framework 7",
            java_version="21 source-kit baseline", verification_suite=proof,
            download_path="/downloads/aitrove-spring-source-kit.zip")
    else:
        row["data"].update(java_release=8, java_version="8+")
    rows.append(row)
    by_path[path] = row
    added.append(path)


put("prefix-sum-range-queries", "Java prefix sums: answer repeated half-open range totals",
    "A prefix-sum array stores cumulative totals so a half-open range [start, end) can be read as prefix[end] minus prefix[start].", [
    ("Define the boundary before coding", ["The first prefix slot is zero. After processing n numbers, prefix has n+1 slots, which makes an empty range legal and avoids a special case at index zero. The program asks for indices one through three, excluding index three. It also checks an empty range, whose total is zero.", "Negative values are fine; a sliding-window rule that assumes nonnegative values would not be interchangeable. [[java/sliding-window|Sliding windows]] answer a different set of questions. Use a long accumulator when int values may add up beyond int range, and define what to do if even long overflows."]),
    ("Updates invalidate the snapshot", ["This structure is for many reads over values that remain fixed. Changing a source element makes later prefix totals stale. [[java/fenwick-tree|Fenwick trees]] cover point updates with prefix queries, while [[java/difference-array-range-updates|difference arrays]] handle a batch of range additions before a final read."])
], '''public class ReceiptPrefixTotals {
    static long range(long[] prefix, int start, int end) {
        if (start < 0 || end < start || end >= prefix.length) throw new IndexOutOfBoundsException();
        return prefix[end] - prefix[start];
    }
    public static void main(String[] args) {
        int[] changes = {4, -2, 7, 1};
        long[] prefix = new long[changes.length + 1];
        for (int index = 0; index < changes.length; index++)
            prefix[index + 1] = Math.addExact(prefix[index], changes[index]);
        System.out.println("range=" + range(prefix, 1, 3));
        System.out.println("empty=" + range(prefix, 2, 2));
    }
}''', 'range=5\nempty=0',
"Building the array takes O(n) time and O(n) additional space; each validated range query takes O(1). The subtraction can still overflow long for arbitrary external data, so a larger numeric policy may be needed.",
["Do not mix inclusive and half-open endpoints.", "Do not mutate the source after building prefixes and use stale totals.", "Do not sum large int batches in an int accumulator."],
["java/sliding-window", "java/fenwick-tree", "java/arrays"])

put("difference-array-range-updates", "Java difference arrays: batch inclusive range additions",
    "A difference array records only the boundaries of each inclusive range addition, then reconstructs the final values with one prefix pass.", [
    ("Mark where a change begins and ends", ["Adding four to positions one through three writes +4 at one and -4 after three. A second update subtracts one from positions two through four. The final scan gives [0, 4, 3, 3, -1]. The test also rejects an inverted interval before changing any boundary.", "The add operation is fast because it postpones materialization. Reading one final value before reconstruction would be wrong. For interleaved online updates and reads, [[java/lazy-segment-tree|lazy segment trees]] or other indexed structures fit better."]),
    ("Know the endpoint convention", ["This page uses inclusive [left, right]. [[java/prefix-sum-range-queries|Prefix-sum queries]] use half-open [start, end). Name that difference at the API boundary; an off-by-one update near the last element is easy to miss."])
], '''import java.util.Arrays;
public class ReceiptRangeAdjustments {
    static void add(long[] difference, int left, int right, long delta) {
        if (left < 0 || right < left || right >= difference.length) throw new IndexOutOfBoundsException();
        difference[left] = Math.addExact(difference[left], delta);
        if (right + 1 < difference.length)
            difference[right + 1] = Math.subtractExact(difference[right + 1], delta);
    }
    public static void main(String[] args) {
        long[] difference = new long[5];
        add(difference, 1, 3, 4);
        add(difference, 2, 4, -1);
        try { add(difference, 4, 2, 9); }
        catch (IndexOutOfBoundsException rejected) { System.out.println("bad interval"); }
        long[] values = new long[difference.length];
        long total = 0;
        for (int index = 0; index < values.length; index++) {
            total = Math.addExact(total, difference[index]);
            values[index] = total;
        }
        System.out.println(Arrays.toString(values));
    }
}''', 'bad interval\n[0, 4, 3, 3, -1]',
"For k validated updates and n final values, this takes O(k+n) time and O(n) difference storage. The two boundary writes are not an atomic transaction if arithmetic or surrounding application work fails partway through.",
["Do not read a point from the unmaterialized difference array as a final value.", "Do not silently mix inclusive and half-open endpoints.", "Do not call two boundary writes a transactional update."],
["java/prefix-sum-range-queries", "java/fenwick-tree", "java/lazy-segment-tree"])

put("next-greater-monotonic-stack", "Java next greater element: keep unresolved indices on a stack",
    "A decreasing stack of unresolved indices lets one left-to-right pass find each position's next strictly greater value.", [
    ("The top is a pending question", ["Each incoming value answers all smaller values at the stack top. Store indices because the output needs positions, not just values. For 4, 1, 3, 5, 2, the next greater indices are 3, 2, 3, -1, -1. An unanswered index remains -1.", "The comparison is strict. Equal values do not answer each other; changing > to >= changes the task. [[java/arraydeque|ArrayDeque]] supplies the stack without the legacy Stack class. [[java/sliding-window-maximum|Window maximum]] uses a deque with a different eviction rule."]),
    ("Amortized work is the point", ["A value can cause several pops, but each index is pushed once and popped at most once. Do not count the inner while loop as n work for every outer iteration. Input values are not modified."])
], '''import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Deque;
public class NextGreaterReceiptLoad {
    static int[] nextGreaterIndex(int[] load) {
        int[] answer = new int[load.length];
        Arrays.fill(answer, -1);
        Deque<Integer> pending = new ArrayDeque<>();
        for (int index = 0; index < load.length; index++) {
            while (!pending.isEmpty() && load[index] > load[pending.peek()])
                answer[pending.pop()] = index;
            pending.push(index);
        }
        return answer;
    }
    public static void main(String[] args) {
        System.out.println(Arrays.toString(nextGreaterIndex(new int[]{4, 1, 3, 5, 2})));
        if (nextGreaterIndex(new int[]{2, 2})[0] != -1) throw new AssertionError("strict comparison");
    }
}''', '[3, 2, 3, -1, -1]',
"The scan takes O(n) time and O(n) worst-case stack and answer space. Each index has at most one push and one pop, despite the nested while loop.",
["Do not replace > with >= unless equal values should count.", "Do not store only values when the answer needs an index.", "Do not claim the while loop makes this quadratic."],
["java/arraydeque", "java/sliding-window", "java/stack-brackets"])

put("sliding-window-maximum", "Java sliding-window maximum: evict expired indices and weaker tails",
    "A deque of candidate indices can report the maximum of every fixed-width window in one pass.", [
    ("Keep only useful candidates", ["Before adding an index, remove a head that has left the current window. Then remove tail indices whose values are no greater than the incoming value: the new index lasts longer and is at least as strong. The head is the maximum for the current window.", "The fixture uses width three and checks that width one returns the original values. Empty input, zero width and width above input length are rejected in this API. [[java/next-greater-monotonic-stack|Next greater elements]] share the monotonic idea but answer a different query."]),
    ("Tie behavior is deliberate", ["Using <= discards older equal values. That is safe for maximum values; if the product needs the earliest index among equal maxima, use a different tie rule and test it. A deque stores indices so expiry is cheap."])
], '''import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Deque;
public class PeakReviewWindow {
    static int[] maxima(int[] load, int width) {
        if (width < 1 || width > load.length) throw new IllegalArgumentException("width");
        int[] answer = new int[load.length - width + 1];
        Deque<Integer> candidates = new ArrayDeque<>();
        for (int index = 0; index < load.length; index++) {
            while (!candidates.isEmpty() && candidates.peekFirst() <= index - width)
                candidates.removeFirst();
            while (!candidates.isEmpty() && load[candidates.peekLast()] <= load[index])
                candidates.removeLast();
            candidates.addLast(index);
            if (index + 1 >= width) answer[index - width + 1] = load[candidates.peekFirst()];
        }
        return answer;
    }
    public static void main(String[] args) {
        int[] load = {2, 5, 1, 4, 6, 3};
        System.out.println(Arrays.toString(maxima(load, 3)));
        if (!Arrays.equals(maxima(load, 1), load)) throw new AssertionError("width one");
    }
}''', '[5, 5, 6, 6]',
"Each index enters and leaves the deque at most once: O(n) time, O(width) candidate space and O(n-width+1) output space. This is for one fixed width, not arbitrary range maximum queries.",
["Do not leave an expired head in the deque.", "Do not assume a tie policy if the answer needs an index rather than a value.", "Do not accept width zero or greater than the input length without an explicit contract."],
["java/sliding-window", "java/next-greater-monotonic-stack", "java/arraydeque"])

put("weighted-interval-scheduling", "Java weighted interval scheduling: end-time sort and predecessor DP",
    "Weighted interval scheduling maximizes total value from nonoverlapping jobs by comparing each job with the best compatible predecessor.", [
    ("Greedy selection is not enough", ["Sorting by finish time solves the unweighted count problem; it can miss a high-value longer job. The fixture sorts by end, then for each job either skips it or adds its value to the best plan ending no later than its start. A job ending exactly when another starts is compatible.", "The program prints fourteen for the four-job fixture and checks a zero-length input. A binary search finds the count of earlier jobs whose end is at most the current start. [[java/greedy-intervals|Greedy intervals]] explains why the unweighted objective is different; [[java/tabulation|tabulation]] covers recurrence storage."]),
    ("State what values mean", ["This fixture accepts integer times and long scores. Negative scores are harmless because skipping all jobs yields zero. Real scheduling may need setup time, resource conflicts or multiple machines; this recurrence does not include them."])
], '''import java.util.Arrays;
import java.util.Comparator;
public class WeightedReviewSlots {
    static final class Job {
        final int start, end; final long value;
        Job(int start, int end, long value) { this.start = start; this.end = end; this.value = value; }
    }
    static long best(Job[] jobs) {
        Job[] ordered = jobs.clone();
        Arrays.sort(ordered, Comparator.comparingInt(job -> job.end));
        long[] best = new long[ordered.length + 1];
        for (int index = 0; index < ordered.length; index++) {
            if (ordered[index].end < ordered[index].start) throw new IllegalArgumentException("interval");
            int low = 0, high = index;
            while (low < high) {
                int middle = (low + high) >>> 1;
                if (ordered[middle].end <= ordered[index].start) low = middle + 1;
                else high = middle;
            }
            best[index + 1] = Math.max(best[index], Math.addExact(ordered[index].value, best[low]));
        }
        return best[ordered.length];
    }
    public static void main(String[] args) {
        Job[] jobs = {new Job(1, 3, 5), new Job(2, 5, 6),
            new Job(4, 6, 5), new Job(6, 7, 4)};
        System.out.println(best(jobs));
        if (best(new Job[0]) != 0) throw new AssertionError("empty plan");
    }
}''', '14',
"Sorting n jobs and finding n predecessors takes O(n log n) time and O(n) additional state. The recurrence assumes one machine and compatibility when prior end <= next start; changing that policy changes the binary-search boundary.",
["Do not reuse unweighted earliest-finish greedy selection for weighted value.", "Do not treat touching endpoints as conflicting when the declared contract allows them.", "Do not ignore score overflow in a long-running planner."],
["java/greedy-intervals", "java/tabulation", "java/binary-search"])

put("bipartite-matching-augment", "Java bipartite matching: reroute an assignment with an augmenting path",
    "An augmenting-path matcher grows a one-to-one worker-to-task assignment by rerouting an earlier assignment when a new worker needs its task.", [
    ("A local greedy pick can block a full match", ["Worker zero accepts tasks zero or one; worker one accepts only zero; worker two accepts one or two. If worker zero takes zero first, worker one must move worker zero to one. The DFS tries that reroute and reaches three assigned tasks.", "The right-side visited array is fresh for each worker's search. Reusing it across workers would hide a valid reroute. Task IDs must be validated against the declared task count before using them as array indices. [[java/max-flow-edmonds-karp|Max flow]] generalizes this assignment view with capacities."]),
    ("This is a baseline matcher", ["The DFS implementation is suited to small graphs and explanation. Large bipartite graphs need stronger algorithms and workload tests. No monetary or fairness objective is encoded: it maximizes cardinality only."])
], '''import java.util.Arrays;
public class ReviewerAssignment {
    static boolean augment(int reviewer, int[][] choices, boolean[] seen, int[] owner) {
        for (int task : choices[reviewer]) {
            if (task < 0 || task >= owner.length) throw new IllegalArgumentException("task id");
            if (seen[task]) continue;
            seen[task] = true;
            if (owner[task] == -1 || augment(owner[task], choices, seen, owner)) {
                owner[task] = reviewer;
                return true;
            }
        }
        return false;
    }
    static int maximum(int[][] choices, int taskCount) {
        int[] owner = new int[taskCount];
        Arrays.fill(owner, -1);
        int assigned = 0;
        for (int reviewer = 0; reviewer < choices.length; reviewer++)
            if (augment(reviewer, choices, new boolean[taskCount], owner)) assigned++;
        return assigned;
    }
    public static void main(String[] args) {
        System.out.println(maximum(new int[][]{{0, 1}, {0}, {1, 2}}, 3));
        if (maximum(new int[][]{{0}, {0}}, 1) != 1) throw new AssertionError("one task");
    }
}''', '3',
"For W reviewers, T tasks and E preference edges, this simple augmenting DFS can take O(W E) time and O(W+T) extra stack, owner and visited space, excluding caller-owned input. Deep reroutes can exhaust the Java call stack. It finds maximum cardinality, not a minimum-cost or fair assignment.",
["Do not keep one seen array for every reviewer search.", "Do not count a first-choice greedy assignment as maximum.", "Do not accept out-of-range task IDs as valid input."],
["java/graph-bfs", "java/topological-sort", "java/greedy-intervals"])

put("max-flow-edmonds-karp", "Java Edmonds-Karp max flow: residual capacity and reverse edges",
    "Edmonds-Karp repeatedly finds a shortest augmenting path in the residual network, then updates forward and reverse capacities.", [
    ("Reverse edges are part of the state", ["A path can later be rerouted. Decreasing only forward capacity would lose the ability to undo an earlier choice; adding the same amount to the reverse edge records that option. The fixture has total source capacity five and reaches flow five. It also checks a disconnected sink, which returns zero.", "This matrix version treats vertices as a small fixed set and capacities as nonnegative longs. A production graph loader must validate vertex IDs, duplicate edges and sums before a flow run. [[java/bipartite-matching-augment|Bipartite matching]] is a related unit-capacity case."]),
    ("Do not confuse flow with a path", ["The result is total throughput under edge capacities, not the number of edges in one route or the cheapest path. [[java/dijkstra|Dijkstra]] answers a different optimization question."])
], '''import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Queue;
public class ReceiptNetworkFlow {
    static long maximum(long[][] capacity, int source, int sink) {
        int size = capacity.length;
        if (size == 0 || source < 0 || sink < 0 || source >= size || sink >= size || source == sink)
            throw new IllegalArgumentException("endpoints");
        long[][] residual = new long[size][size];
        for (int from = 0; from < size; from++) {
            if (capacity[from].length != size) throw new IllegalArgumentException("square matrix");
            for (int to = 0; to < size; to++) {
                if (capacity[from][to] < 0) throw new IllegalArgumentException("capacity");
                residual[from][to] = capacity[from][to];
            }
        }
        long flow = 0;
        while (true) {
            int[] parent = new int[size];
            Arrays.fill(parent, -1);
            parent[source] = source;
            Queue<Integer> queue = new ArrayDeque<>();
            queue.add(source);
            while (!queue.isEmpty() && parent[sink] == -1) {
                int from = queue.remove();
                for (int to = 0; to < size; to++)
                    if (parent[to] == -1 && residual[from][to] > 0) {
                        parent[to] = from;
                        queue.add(to);
                    }
            }
            if (parent[sink] == -1) return flow;
            long amount = Long.MAX_VALUE;
            for (int to = sink; to != source; to = parent[to])
                amount = Math.min(amount, residual[parent[to]][to]);
            for (int to = sink; to != source; to = parent[to]) {
                int from = parent[to];
                residual[from][to] -= amount;
                residual[to][from] = Math.addExact(residual[to][from], amount);
            }
            flow = Math.addExact(flow, amount);
        }
    }
    public static void main(String[] args) {
        long[][] network = {{0, 3, 2, 0}, {0, 0, 1, 2},
            {0, 0, 0, 3}, {0, 0, 0, 0}};
        System.out.println(maximum(network, 0, 3));
        if (maximum(new long[][]{{0, 0}, {0, 0}}, 0, 1) != 0)
            throw new AssertionError("disconnected sink");
    }
}''', '5',
"Edmonds-Karp has O(V E²) time for an adjacency-list graph. This matrix version scans V neighbors for each vertex: with O(V E) augmentations, its upper bound is O(V² + V³ E) time and O(V²) residual space. E counts positive-capacity arcs; sparse production graphs need a different representation.",
["Do not omit reverse residual capacity.", "Do not treat negative or overflowing capacities as valid input.", "Do not report a matrix scan as if it used an adjacency list."],
["java/graph-bfs", "java/bipartite-matching-augment", "java/dijkstra"])

put("a-star-unit-grid", "Java A* on a unit grid: an admissible Manhattan bound",
    "A* orders candidate grid cells by distance-so-far plus a lower bound to the goal; on a four-neighbor unit-cost grid, Manhattan distance is such a bound.", [
    ("Keep the cost and heuristic separate", ["Each open cell move costs one. The fixture blocks the center of a three-by-three grid, so a route from the upper-left to the lower-right takes four moves. A second fixture blocks both exits from the start and returns -1. The priority queue may contain stale entries; the code skips an entry when its stored cost no longer matches the best known distance.", "Manhattan distance stops being a valid lower bound if the graph admits a cheaper diagonal or teleport move. For zero heuristic, this becomes a Dijkstra-style search. [[java/dijkstra|Dijkstra]] covers weighted edges without a spatial bound."]),
    ("A shortest length is not a path", ["This page returns distance only. To show the actual route, record a predecessor for each improvement and reconstruct it after reaching the goal. A map service also needs movement rules and blocked-cell data that do not change halfway through a search."])
], '''import java.util.Arrays;
import java.util.Comparator;
import java.util.PriorityQueue;
public class ReviewGridRoute {
    static final class Step {
        final int row, col, cost, score;
        Step(int row, int col, int cost, int score) {
            this.row = row; this.col = col; this.cost = cost; this.score = score;
        }
    }
    static int shortest(boolean[][] blocked) {
        if (blocked == null || blocked.length == 0 || blocked[0] == null || blocked[0].length == 0)
            throw new IllegalArgumentException("nonempty grid");
        int rows = blocked.length, cols = blocked[0].length;
        for (boolean[] line : blocked)
            if (line == null || line.length != cols) throw new IllegalArgumentException("rectangular grid");
        if (blocked[0][0] || blocked[rows - 1][cols - 1]) return -1;
        int[][] best = new int[rows][cols];
        for (int[] line : best) Arrays.fill(line, Integer.MAX_VALUE);
        best[0][0] = 0;
        PriorityQueue<Step> open = new PriorityQueue<>(Comparator.comparingInt(step -> step.score));
        open.add(new Step(0, 0, 0, rows + cols - 2));
        int[][] moves = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
        while (!open.isEmpty()) {
            Step current = open.remove();
            if (current.cost != best[current.row][current.col]) continue;
            if (current.row == rows - 1 && current.col == cols - 1) return current.cost;
            for (int[] move : moves) {
                int row = current.row + move[0], col = current.col + move[1];
                if (row < 0 || row >= rows || col < 0 || col >= cols || blocked[row][col]) continue;
                int next = current.cost + 1;
                if (next < best[row][col]) {
                    best[row][col] = next;
                    int bound = Math.abs(rows - 1 - row) + Math.abs(cols - 1 - col);
                    open.add(new Step(row, col, next, next + bound));
                }
            }
        }
        return -1;
    }
    public static void main(String[] args) {
        System.out.println(shortest(new boolean[][]{{false, false, false},
            {false, true, false}, {false, false, false}}));
        if (shortest(new boolean[][]{{false, true}, {true, false}}) != -1)
            throw new AssertionError("blocked exits");
    }
}''', '4',
"For V cells and at most four neighbors per cell, the priority queue and best-distance array take O(V) stored states in the usual simple-grid case; queue operations give O(V log V) time. This fixture rejects empty and ragged grids but does not support weighted or diagonal movement, map changes, or large-grid memory pressure.",
["Do not reuse Manhattan distance when cheaper diagonal or teleport edges exist.", "Do not process stale queue entries as new shortest paths.", "Do not report a distance as if the actual route was reconstructed.", "Do not accept a ragged grid and index it as if every row had the same length."],
["java/dijkstra", "java/graph-bfs", "java/priorityqueue"])

put("if-match-receipt-write", "Spring If-Match writes: reject a stale receipt revision",
    "A conditional write compares the client's representation tag with the current revision before applying a state change.", [
    ("The stale client does not overwrite", ["The checked controller starts at receipt version one. PUT without If-Match gets 428 under this fixture's API policy; a stale tag gets 412. The current tag permits a write and creates version two. Reusing the old tag then fails and the stored state remains reviewed.", "The code supports one quoted strong tag. Full HTTP If-Match syntax includes other forms and requires an HTTP-aware implementation. [[spring/conditional-receipt-get|Conditional GET]] validates a read cache; a write precondition protects an update. Neither grants authorization."]),
    ("The in-memory lock is not a database lock", ["The fixture synchronizes one controller object so its check and update are one local critical section. Two server instances would have independent state and locks. A persisted service needs a database compare-and-set or optimistic version check inside the write transaction. [[spring/jpa-optimistic-locking|JPA optimistic locking]] covers one such persistence boundary."])
], '''@PutMapping(path = "/contract/revisions/{id}", consumes = "text/plain")
synchronized ResponseEntity<String> update(@PathVariable int id,
    @RequestHeader(value = "If-Match", required = false) String expected,
    @RequestBody String nextState) {
    if (id != 7) return ResponseEntity.notFound().build();
    if (expected == null) return ResponseEntity.status(428).build();
    String current = "\"receipt-7-v" + version + "\"";
    if (!current.equals(expected)) return ResponseEntity.status(412).eTag(current).build();
    state = nextState;
    version++;
    return ResponseEntity.ok().eTag("receipt-7-v" + version).body(state);
}''', "",
"MockMvc tests one local controller instance and its serial state. It does not prove full HTTP tag parsing, concurrent writes across processes, persistent revision checks, authorization, or retry idempotency.",
["Do not accept a stale tag and silently overwrite current state.", "Do not use an in-memory synchronized method as a distributed compare-and-set.", "Do not treat an ETag as evidence that a caller owns the receipt."],
["spring/conditional-receipt-get", "spring/jpa-optimistic-locking", "spring/tenant-receipt-authorization"],
spring=True, proof="ReceiptIfMatchWriteTest.staleClientCannotOverwriteTheCurrentRevision")

for subject, title in (("java-dsa", "Range queries, monotonic structures and graph optimization"),
                       ("spring-web", "Conditional receipt writes")):
    hub = next(row for row in rows if row["type"] == "subject" and row["subject"] == subject)
    lessons = [path for path in added if by_path[path]["subject"] == subject]
    hub["data"]["modules"].append({"title": title,
        "summary": "Check the invariant, run the fixture and test a rejected boundary.", "lessons": lessons})
    hub["updated_at"] = stamp
    if subject == "spring-web":
        links = "<ul>" + "".join('<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>"
            for module in hub["data"]["modules"] for path in module["lessons"]) + "</ul>"
        hub["body"] = re.sub(r"(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)",
            lambda match: match[1] + links + match[2], hub["body"])

reverse = {
    "java/sliding-window": ["java/prefix-sum-range-queries", "java/sliding-window-maximum"],
    "java/fenwick-tree": ["java/prefix-sum-range-queries", "java/difference-array-range-updates"],
    "java/arraydeque": ["java/next-greater-monotonic-stack", "java/sliding-window-maximum"],
    "java/greedy-intervals": ["java/weighted-interval-scheduling"],
    "java/graph-bfs": ["java/bipartite-matching-augment", "java/max-flow-edmonds-karp", "java/a-star-unit-grid"],
    "java/dijkstra": ["java/a-star-unit-grid", "java/max-flow-edmonds-karp"],
    "spring/conditional-receipt-get": ["spring/if-match-receipt-write"],
    "spring/jpa-optimistic-locking": ["spring/if-match-receipt-write"],
}
for path, targets in reverse.items():
    row = by_path[path]
    marker = "<h2>Continue with range and graph boundaries</h2>"
    row["body"] = row["body"].split(marker)[0] + marker + para("Continue with " + ", ".join(
        "[[" + target + "|" + by_path[target]["title"] + "]]" for target in targets) + ".")
    row["updated_at"] = stamp

FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"added": added, "count": len(added)}))
