"""Add checked Java node algorithms and runtime boundary tutorials."""

import copy
import datetime
import html
import json
import pathlib
import re
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILE = ROOT / "src/data/fixtures.json"
entries = json.loads(FILE.read_text())
lookup = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
added = []


def paragraph(value):
    escaped = html.escape(value)
    return "<p>" + re.sub(
        r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>",
        escaped,
    ) + "</p>"


def block(value, language="java"):
    return '<pre><code class="language-' + language + '">' + html.escape(value.strip(), quote=False) + "</code></pre>"


def add(slug, title, definition, sections, source, output, cost, mistakes, related, subject="java-dsa", release=8):
    path = "java/" + slug
    body = paragraph(definition)
    for heading, paragraphs in sections:
        body += "<h2>" + heading + "</h2>" + "".join(paragraph(item) for item in paragraphs)
    body += "<h2>Working program</h2>" + block(source)
    if output is not None:
        body += "<h3>Output</h3>" + block(output, "text")
    body += "<h2>Cost and ownership</h2>" + paragraph(cost)
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in mistakes) + "</ul>"
    body += "<h2>Read next</h2>" + paragraph(
        ", ".join("[[" + item + "|" + lookup.get(item, {}).get("title", item.rsplit("/", 1)[-1].replace("-", " ")) + "]]" for item in related) + "."
    )
    entry = copy.deepcopy(lookup["java/casts"])
    entry.update(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
        path=path,
        title=title,
        summary=definition,
        body=body,
        subject=subject,
        category="Programming",
        tags=["java", slug],
        difficulty="Intermediate",
        sort_order=950 + len(added),
        status="published",
        featured=False,
        published_at=stamp,
        created_at=stamp,
        updated_at=stamp,
    )
    entry["data"] = {
        "subject_root": "java/java",
        "section_path": next(item["path"] for item in entries if item["type"] == "subject" and item["subject"] == subject),
        "kind": "tutorial",
        "content_format": "html",
        "reading_minutes": max(4, round(len(re.sub("<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial",
        "related": [],
        "seo_ready": True,
        "java_release": release,
        "java_version": str(release) + "+",
    }
    entry["_related_paths"] = related
    if path in lookup:
        entries[entries.index(lookup[path])] = entry
    else:
        entries.append(entry)
    lookup[path] = entry
    added.append(path)


add(
    "reverse-singly-linked-chain",
    "Reverse a singly linked chain in Java without allocating new nodes",
    "Reversing a singly linked chain changes each node's next reference so the former tail becomes the new head.",
    [
        ("Keep three references alive", [
            "A node exposes only its successor. Save that successor before changing the link; otherwise the unvisited suffix becomes unreachable from the current traversal. At each step, current.next points to the already reversed prefix, and previous advances to current. When current becomes null, previous is the new head.",
            "This is an algorithm for an application-owned Node chain. java.util.LinkedList does not expose its internal nodes. To inspect that collection backward, use [[java/linkedlist-reverse-traversal|descendingIterator]] or a reversed view where supported; rebuilding a list by repeated indexed access would pay for repeated link walks."
        ]),
        ("State the precondition", [
            "The input must be acyclic. A cycle would prevent the loop from reaching null and would mutate the cycle while it ran. If the chain comes from untrusted graph construction, run [[java/linked-cycle-entry|cycle detection]] first. The method also works for null and a single node, which makes those useful boundary fixtures.",
            "Reversal changes the caller's chain. Any old head reference now identifies the tail. If another owner still uses the old head as though it represented the whole sequence, it sees a truncated path; return and publish the new head as one ownership change."
        ]),
    ],
    '''public class ReverseDispatchChain {
    static final class Node {
        final String dispatchId;
        Node next;
        Node(String dispatchId, Node next) { this.dispatchId = dispatchId; this.next = next; }
    }
    static Node reverse(Node head) {
        Node previous = null;
        Node current = head;
        while (current != null) {
            Node following = current.next;
            current.next = previous;
            previous = current;
            current = following;
        }
        return previous;
    }
    static String labels(Node head) {
        StringBuilder result = new StringBuilder();
        for (Node current = head; current != null; current = current.next) {
            if (result.length() > 0) result.append(",");
            result.append(current.dispatchId);
        }
        return result.toString();
    }
    public static void main(String[] args) {
        Node head = new Node("load-47", new Node("seal-82", new Node("ship-15", null)));
        System.out.println(labels(reverse(head)));
        System.out.println(reverse(null) == null);
    }
}''',
    "ship-15,seal-82,load-47\ntrue",
    "One pass visits n nodes in O(n) time and holds O(1) extra node references. It does not copy payload objects. The method is not safe to run while another thread traverses or mutates the same chain without an ownership or synchronization boundary.",
    ["Do not overwrite current.next before saving the next unvisited node.", "Do not keep using the old head as the root after reversal.", "Do not run a null-terminated loop on a chain that may contain a cycle."],
    ["java/linked-cycle-entry", "java/linked-palindrome-restore", "java/linkedlist", "java/linkedlist-reverse-traversal"],
)

add(
    "linked-cycle-entry",
    "Find the entry of a cycle in a Java singly linked chain",
    "A fast and a slow pointer can detect a cycle, then locate its entry without storing visited nodes.",
    [
        ("Detect before locating", [
            "Move one pointer by one link and the other by two. If either reaches null, the chain terminates. If they meet, a cycle exists. A meeting node is not necessarily the entry. Reset one pointer to the head and move both one link at a time; their next meeting is the first node on the cycle.",
            "The second walk follows from distances: after the first meeting, the head-to-entry distance and the meeting-to-entry distance differ by a whole number of cycle lengths. Advancing both at the same rate removes that difference. The fixture connects a tail back to an internal dispatch ID and separately checks an acyclic chain."
        ]),
        ("Choose the right container", [
            "This algorithm applies when code owns next references. Java's [[java/linkedlist|LinkedList collection]] keeps those references private, so its public API cannot expose a cycle entry. A collection cannot be made cyclic through ordinary List operations. The distinction matters when interview pseudocode is pasted into production code that actually holds a List<String>.",
            "Before [[java/reverse-singly-linked-chain|reversing]] or [[java/merge-sorted-linked-chains|merging]] a custom chain, reject cycles or establish acyclicity at construction. Otherwise a traversal meant to be linear can run indefinitely."
        ]),
    ],
    '''public class DispatchCycleEntry {
    static final class Node {
        final String dispatchId;
        Node next;
        Node(String dispatchId) { this.dispatchId = dispatchId; }
    }
    static Node entry(Node head) {
        Node slow = head, fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
            if (slow == fast) {
                Node fromHead = head;
                while (fromHead != slow) {
                    fromHead = fromHead.next;
                    slow = slow.next;
                }
                return fromHead;
            }
        }
        return null;
    }
    public static void main(String[] args) {
        Node intake = new Node("intake-47");
        Node verify = new Node("verify-82");
        Node ship = new Node("ship-15");
        intake.next = verify; verify.next = ship; ship.next = verify;
        System.out.println(entry(intake).dispatchId);
        ship.next = null;
        System.out.println(entry(intake) == null);
    }
}''',
    "verify-82\ntrue",
    "Detection and entry search each take at most O(n) link visits, with O(1) extra references. The algorithm reads node identity, not payload equality; two records with the same dispatch ID are still distinct nodes.",
    ["Do not return the first fast/slow meeting point as the entry without the second walk.", "Do not compare dispatch ID values to decide whether two pointers meet.", "Do not dereference fast.next.next before checking both fast and fast.next."],
    ["java/reverse-singly-linked-chain", "java/merge-sorted-linked-chains", "java/linkedlist", "java/graph-dfs"],
)

add(
    "merge-sorted-linked-chains",
    "Merge two sorted Java node chains by moving their links",
    "A sorted merge selects the smaller current head from two acyclic chains and appends that existing node to the result.",
    [
        ("Consume two owners", [
            "The inputs are sorted by priority, acyclic, and disjoint: no node belongs to both. That last precondition is easy to miss. If both inputs share a suffix, relinking one path can create a cycle or duplicate references. The merge consumes the input chains as independent roots; callers should use only the returned head afterward.",
            "When priorities tie, the code takes the left node first. That preserves each input's order and makes the merge stable across the two sources. It does not sort either source; a single misplaced priority in an input invalidates the output ordering. [[java/merge-sort|Merge sort]] uses the same merge idea after it has created sorted runs."
        ]),
        ("Account for tail work", [
            "Once one input is empty, attach the remaining suffix in one link change. There is no need to copy or walk that suffix again. The dummy head simplifies the first append and adds one temporary node; a production implementation can avoid it if allocation is a concern.",
            "This is not the same as calling addAll on two java.util.LinkedList objects. The JDK collection owns private nodes and may allocate nodes for the destination. [[java/linkedlist-addall-alias|Aliased addAll input]] has a separate, explicitly documented boundary."
        ]),
    ],
    '''public class MergeDispatchPriorities {
    static final class Node {
        final int priority;
        final String dispatchId;
        Node next;
        Node(int priority, String dispatchId, Node next) {
            this.priority = priority; this.dispatchId = dispatchId; this.next = next;
        }
    }
    static Node merge(Node left, Node right) {
        Node sentinel = new Node(Integer.MIN_VALUE, "sentinel", null);
        Node tail = sentinel;
        while (left != null && right != null) {
            if (left.priority <= right.priority) {
                Node selected = left; left = left.next; tail.next = selected;
            } else {
                Node selected = right; right = right.next; tail.next = selected;
            }
            tail = tail.next;
        }
        tail.next = left != null ? left : right;
        return sentinel.next;
    }
    static String labels(Node head) {
        StringBuilder result = new StringBuilder();
        for (Node current = head; current != null; current = current.next) {
            if (result.length() > 0) result.append(",");
            result.append(current.dispatchId);
        }
        return result.toString();
    }
    public static void main(String[] args) {
        Node left = new Node(11, "left-11", new Node(47, "left-47", null));
        Node right = new Node(11, "right-11", new Node(32, "right-32", null));
        System.out.println(labels(merge(left, right)));
    }
}''',
    "left-11,right-11,right-32,left-47",
    "For n and m input nodes, the merge performs O(n + m) comparisons and link visits with O(1) extra node storage. The dummy node is not part of the returned chain. Input nodes are reused, so the caller gives up independent ownership of both old roots.",
    ["Do not merge chains that share a node or contain cycles.", "Do not assume the method repairs unsorted inputs.", "Do not keep mutating an old input root as though it still names a separate chain."],
    ["java/linked-cycle-entry", "java/reverse-singly-linked-chain", "java/merge-sort", "java/linkedlist-addall-alias"],
)

add(
    "linked-palindrome-restore",
    "Check a Java linked palindrome and restore the original links",
    "A linked-chain palindrome check compares the first half with a reversed second half, then reverses that half again before returning.",
    [
        ("Treat temporary mutation as an obligation", [
            "A slow pointer locates the middle while a fast pointer advances twice as quickly. For odd lengths, the middle node is excluded from comparison. Reverse the second half, compare corresponding IDs, and restore the same links in a finally block even when a mismatch returns early. The fixture checks both an odd palindrome and a non-palindrome, then prints the latter chain to prove its links were restored.",
            "The algorithm assumes an acyclic chain and exclusive access while it runs. During comparison, the second half is temporarily pointed backward; another reader could see a truncated or malformed path. [[java/linked-cycle-entry|Cycle detection]] and an ownership rule belong before this method in a shared structure."
        ]),
        ("Keep the comparison contract small", [
            "The code compares non-null dispatch IDs by String.equals. Null identifiers are rejected at node construction in a real domain model; this fixture uses literal IDs to keep the link algorithm visible. If equality means case folding or Unicode normalization, perform that policy at input rather than quietly changing the palindrome relation here.",
            "A java.util.LinkedList offers a descending iterator, but it does not expose internal nodes for half reversal. A two-iterator comparison can be simpler when O(1) extra space is not an interview constraint. [[java/linkedlist-reverse-traversal|Reverse traversal]] documents that API route."
        ]),
    ],
    '''public class DispatchPalindromeCheck {
    static final class Node {
        final String dispatchId;
        Node next;
        Node(String dispatchId, Node next) { this.dispatchId = dispatchId; this.next = next; }
    }
    static Node reverse(Node head) {
        Node previous = null;
        for (Node current = head; current != null; ) {
            Node following = current.next;
            current.next = previous;
            previous = current;
            current = following;
        }
        return previous;
    }
    static boolean isPalindrome(Node head) {
        Node slow = head, fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
        }
        Node secondHalf = fast == null ? slow : slow.next;
        Node reversed = reverse(secondHalf);
        try {
            Node left = head, right = reversed;
            while (right != null) {
                if (!left.dispatchId.equals(right.dispatchId)) return false;
                left = left.next; right = right.next;
            }
            return true;
        } finally {
            reverse(reversed);
        }
    }
    static String labels(Node head) {
        StringBuilder result = new StringBuilder();
        for (Node current = head; current != null; current = current.next) {
            if (result.length() > 0) result.append(",");
            result.append(current.dispatchId);
        }
        return result.toString();
    }
    public static void main(String[] args) {
        Node matching = new Node("scan", new Node("seal", new Node("scan", null)));
        Node different = new Node("scan", new Node("seal", new Node("ship", null)));
        System.out.println(isPalindrome(matching));
        System.out.println(isPalindrome(different));
        System.out.println(labels(different));
        System.out.println(isPalindrome(null));
    }
}''',
    "true\nfalse\nscan,seal,ship\ntrue",
    "The middle scan, half reversal, comparison, and restoration together take O(n) time and O(1) auxiliary node references. The method mutates links temporarily; it is unsuitable for unsynchronized shared reads even though the final visible chain is restored.",
    ["Do not forget the restore step on a mismatch.", "Do not compare the middle node against itself for odd lengths.", "Do not run this algorithm on a cyclic or concurrently traversed chain."],
    ["java/reverse-singly-linked-chain", "java/linked-cycle-entry", "java/linkedlist-reverse-traversal", "java/text-normalization"],
)

add(
    "array-copy-ownership",
    "Java array copies: new slots can still point at old objects",
    "Arrays.copyOf creates a new array, but an object-array copy retains references to the same element objects.",
    [
        ("Separate slot ownership from element ownership", [
            "Replacing a source array slot does not replace the corresponding copied slot. Mutating an object that both slots still reference is different: both arrays observe the object's new state. The fixture performs both changes so the two ownership boundaries are visible in the output.",
            "The same shallow-copy issue appears when a record holds an array and when a LinkedList clone copies nodes but shares elements. [[java/record-defensive-copy|Defensive record copies]] and [[java/linkedlist-shallow-copy|LinkedList cloning]] cover those callers."
        ]),
        ("Choose a domain copy deliberately", [
            "If a caller must own a frozen snapshot of mutable shipments, create new immutable value objects or copy each mutable element under a defined constructor. A second array alone is insufficient. The exact copy depth depends on the object graph and alias policy; a generic recursive copy routine cannot infer which shared references are intentional.",
            "Arrays.copyOf also pads a longer copy with null elements. Validate a requested length before allocating, and do not assume the extra slots contain usable records. [[java/arrays|Array bounds]] explains the index contract."
        ]),
    ],
    '''import java.util.Arrays;

public class ShipmentArrayOwnership {
    static final class Shipment {
        String state;
        Shipment(String state) { this.state = state; }
    }
    public static void main(String[] args) {
        Shipment sharedShipment = new Shipment("queued");
        Shipment[] live = {sharedShipment};
        Shipment[] snapshotSlots = Arrays.copyOf(live, live.length);
        live[0] = new Shipment("manual-review");
        System.out.println(snapshotSlots[0].state);
        sharedShipment.state = "sent";
        System.out.println(snapshotSlots[0].state);
        System.out.println(live[0].state);
    }
}''',
    "queued\nsent\nmanual-review",
    "Copying n references takes O(n) time and O(n) additional slots. It does not allocate n new Shipment objects. A deeper copy has extra allocation and must state how nested references, cycles, and shared identities are handled.",
    ["Do not call an object-array copy an immutable snapshot of its elements.", "Do not assume a longer copy has initialized domain values in padded slots.", "Do not expose a caller-owned array from a supposedly immutable object."],
    ["java/arrays", "java/record-defensive-copy", "java/linkedlist-shallow-copy", "java/pass-by-value"],
    "java",
)

add(
    "checked-integer-arithmetic",
    "Java checked integer arithmetic: reject overflow before updating state",
    "Math.addExact computes an int or long sum and throws ArithmeticException instead of silently wrapping an out-of-range result.",
    [
        ("Calculate before publishing", [
            "A counter near Integer.MAX_VALUE can wrap negative with ordinary addition. In inventory or billing state, that is not a harmless numerical oddity: later bounds checks may accept a wrong value. Compute the candidate with addExact first, then assign it to the live counter. The program reaches the int maximum exactly and rejects one more unit without changing the stored count.",
            "A wider long delays overflow but does not remove it. For unbounded mathematical totals, choose BigInteger; for decimal amounts, use an explicit [[java/bigdecimal|BigDecimal policy]]. [[java/operators|Numeric promotion]] matters before the checked call: an overflowing expression inside an argument may already be wrong by the time addExact sees it."
        ]),
        ("Make failure part of the API", [
            "This small counter rejects a negative increment and exposes a read method. A real shared counter also needs synchronization or an atomic state transition; addExact alone does not make a read-modify-write thread-safe. [[java/atomics|Atomic variables]] and [[java/locks|locks]] cover that separate problem.",
            "Multiplication, subtraction, narrowing to int, and increment have corresponding exact methods. Use the operation matching the domain rule rather than testing after a wrapped value has escaped into another object."
        ]),
    ],
    '''public class CheckedStockCounter {
    static final class StockCounter {
        private int received;
        StockCounter(int received) { this.received = received; }
        void add(int units) {
            if (units < 0) throw new IllegalArgumentException("negative units");
            int candidate = Math.addExact(received, units);
            received = candidate;
        }
        int received() { return received; }
    }
    public static void main(String[] args) {
        StockCounter counter = new StockCounter(2_147_483_600);
        counter.add(47);
        System.out.println(counter.received());
        try { counter.add(1); }
        catch (ArithmeticException rejected) { System.out.println("overflow rejected"); }
        System.out.println(counter.received());
    }
}''',
    "2147483647\noverflow rejected\n2147483647",
    "Each checked primitive operation has O(1) time and storage cost. This example protects arithmetic correctness for one thread; a concurrent counter requires an additional atomicity boundary around the read, calculation, and write.",
    ["Do not check an int after it has already wrapped and call that overflow protection.", "Do not assume long is mathematically unbounded.", "Do not confuse exact arithmetic with concurrent atomic updates."],
    ["java/operators", "java/atomics", "java/locks", "java/bigdecimal"],
    "java",
)

add(
    "generic-varargs-boundary",
    "Java generic varargs: audit the hidden array before using SafeVarargs",
    "A generic varargs parameter is represented by an array whose runtime component type cannot fully represent its parameterized element type.",
    [
        ("Keep the temporary array private", [
            "A method taking List<? extends T>... receives an array of lists. If it writes an incompatible list through an Object[] alias or returns that array to a caller, a later read can fail far from the write. The checked method only reads each list and copies its values into a fresh result. It does not store the array or expose it.",
            "@SafeVarargs is an assertion by the method author, not a compiler proof that arbitrary body code is safe. In Java 8 it may annotate a static or final method. Audit any later edit to the method before keeping the annotation. [[java/generics|Erasure and bounds]] and [[java/varargs|array call boundaries]] supply the two rules behind this case."
        ]),
        ("Decide how much to copy", [
            "The result is a new List, but its values are the same referenced objects from the inputs. That is enough for immutable String dispatch IDs. If the inputs contain mutable orders, a caller cannot claim a deep snapshot. [[java/array-copy-ownership|Array copy ownership]] shows the same distinction in a simpler container.",
            "Reject a null batch rather than letting an incidental NullPointerException surface inside a traversal. A live input list modified concurrently has no stable snapshot guarantee; copy or synchronize at the caller boundary."
        ]),
    ],
    '''import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class DispatchBatchUnion {
    @SafeVarargs
    static <T> List<T> snapshot(List<? extends T>... batches) {
        List<T> result = new ArrayList<>();
        for (List<? extends T> batch : batches) {
            if (batch == null) throw new IllegalArgumentException("null batch");
            result.addAll(batch);
        }
        return result;
    }
    public static void main(String[] args) {
        List<String> north = Arrays.asList("dispatch-47", "dispatch-82");
        List<String> south = Arrays.asList("dispatch-15");
        System.out.println(snapshot(north, south));
    }
}''',
    "[dispatch-47, dispatch-82, dispatch-15]",
    "Copying k references across all batches takes O(k) time and O(k) result storage. The hidden varargs array is short-lived and not returned. The method does not copy or freeze the elements, and result allocation can still fail for very large inputs.",
    ["Do not annotate a varargs method as safe after it writes through an Object[] alias.", "Do not return or retain the varargs array as a supposedly typed collection.", "Do not mistake a new outer List for copies of mutable elements."],
    ["java/generics", "java/varargs", "java/array-copy-ownership", "java/collection-views"],
    "java-advanced",
)

add(
    "completion-service-order",
    "Java ExecutorCompletionService: consume finished tasks, not submission order",
    "ExecutorCompletionService submits work to an owned executor and queues completed Future results in completion order.",
    [
        ("Wait for the result that exists", [
            "Reading a List<Future> in submission order can block on a slow first task while a later task is ready. A completion service separates submission from result consumption. The fixture holds the first task behind a latch, then submits a second task that completes; take returns the second result first. It releases the first task before taking its result.",
            "This ordering is an availability choice, not an ordering guarantee for a report. If the final output must match request order, retain a stable identifier and reorder after collecting. A failed task still yields a completed Future; get throws its ExecutionException, so a consumer must decide whether to continue or stop."
        ]),
        ("Own every submitted task", [
            "The completion queue can retain finished results until the caller drains them. Submitting an unbounded stream without draining or limiting admission can grow memory even with a fixed worker count. The program submits exactly two tasks, collects exactly two results, and shuts down its executor in finally.",
            "[[java/executors|Executor ownership]] covers shutdown, [[java/completable-future|future composition]] handles dependency chains, and [[java/completablefuture-timeout-work|timeouts]] do not necessarily stop a worker. Those are different contracts."
        ]),
    ],
    '''import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorCompletionService;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class FinishedDispatchFirst {
    public static void main(String[] args) throws Exception {
        ExecutorService workers = Executors.newFixedThreadPool(2);
        CountDownLatch slowStarted = new CountDownLatch(1);
        CountDownLatch releaseSlow = new CountDownLatch(1);
        try {
            ExecutorCompletionService<String> completed = new ExecutorCompletionService<>(workers);
            completed.submit(() -> {
                slowStarted.countDown();
                if (!releaseSlow.await(2, TimeUnit.SECONDS)) throw new IllegalStateException("release deadline");
                return "slow-47";
            });
            if (!slowStarted.await(2, TimeUnit.SECONDS)) throw new IllegalStateException("start deadline");
            completed.submit(() -> "fast-82");
            System.out.println(completed.take().get());
            releaseSlow.countDown();
            System.out.println(completed.take().get());
        } finally {
            releaseSlow.countDown();
            workers.shutdown();
            if (!workers.awaitTermination(2, TimeUnit.SECONDS)) workers.shutdownNow();
        }
    }
}''',
    "fast-82\nslow-47",
    "With a fixed two-task fixture, work scheduling is bounded. For n submitted tasks, the completion service can retain O(n) completed Future references until consumption. The executor's queue and the completion queue are distinct memory owners, so a production producer needs an admission limit.",
    ["Do not read submitted Future objects in input order when the goal is first available output.", "Do not forget to drain completed results or bound submissions.", "Do not treat a completed Future as a successful task without calling get."],
    ["java/executors", "java/completable-future", "java/completablefuture-timeout-work", "java/executor-rejection"],
    "java-advanced",
)

add(
    "threadpool-caller-runs",
    "Java CallerRunsPolicy: a full worker queue moves work onto the submitter",
    "ThreadPoolExecutor.CallerRunsPolicy executes a rejected task on the thread calling execute while the executor is running.",
    [
        ("Make saturation observable", [
            "The fixture holds one worker in a latch and fills its single queued slot. A third execute call then runs on main. This slows submission, but it also moves arbitrary task work into the caller's latency budget. An HTTP request thread could spend its deadline processing background work if this policy were copied into a server without thought.",
            "The policy discards a rejected task if the executor is already shut down. That is a poor default where every accepted order must receive a durable outcome. [[java/executor-rejection|Explicit rejection handling]] is the safer contract for those workflows."
        ]),
        ("Size both queues", [
            "A fixed worker count does not cap retained work if its queue is unbounded. Here both worker count and queue size are one, so the third submission must meet the policy. The latch makes this deterministic; a sleep-based demo would depend on machine speed.",
            "The result proves where the third task ran, not that caller execution is always suitable. Blocking tasks, thread-local request state, and nested submissions can create latency or deadlock paths. [[java/thread-local-cleanup|Thread-local cleanup]] matters when code runs on a different thread than expected."
        ]),
    ],
    '''import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

public class SaturatedDispatchPool {
    public static void main(String[] args) throws Exception {
        ThreadPoolExecutor workers = new ThreadPoolExecutor(1, 1, 0L, TimeUnit.MILLISECONDS,
            new ArrayBlockingQueue<>(1), new ThreadPoolExecutor.CallerRunsPolicy());
        CountDownLatch firstStarted = new CountDownLatch(1);
        CountDownLatch releaseFirst = new CountDownLatch(1);
        CountDownLatch queuedFinished = new CountDownLatch(1);
        AtomicReference<Thread> overflowThread = new AtomicReference<>();
        try {
            workers.execute(() -> {
                firstStarted.countDown();
                try { releaseFirst.await(); }
                catch (InterruptedException stopped) { Thread.currentThread().interrupt(); }
            });
            if (!firstStarted.await(2, TimeUnit.SECONDS)) throw new IllegalStateException("start deadline");
            workers.execute(queuedFinished::countDown);
            workers.execute(() -> overflowThread.set(Thread.currentThread()));
            System.out.println(overflowThread.get() == Thread.currentThread());
            releaseFirst.countDown();
            System.out.println(queuedFinished.await(2, TimeUnit.SECONDS));
        } finally {
            releaseFirst.countDown();
            workers.shutdown();
            if (!workers.awaitTermination(2, TimeUnit.SECONDS)) workers.shutdownNow();
        }
    }
}''',
    "true\ntrue",
    "The executor holds one active and one queued task in this fixture; overflow work uses the caller's time and stack. CallerRunsPolicy is feedback through latency, not a persisted admission record. If the caller abandons the request, the application still needs an outcome policy for its work.",
    ["Do not assume a fixed worker count also bounds an unbounded task queue.", "Do not use CallerRunsPolicy where submitter latency is hard-bounded without accounting for task duration.", "Do not assume shutdown submissions are executed; this policy discards them."],
    ["java/executor-rejection", "java/executors", "java/completion-service-order", "java/thread-local-cleanup"],
    "java-advanced",
)

add(
    "path-lexical-boundary",
    "Java Path.normalize: reject lexical escapes without promising symlink safety",
    "Path.normalize removes redundant name elements lexically; it does not read the filesystem or prove that a path stays inside a directory after symlinks are followed.",
    [
        ("Check the requested name", [
            "A caller-supplied relative name can contain .. segments that walk above an intended root. Resolve it against an absolute normalized root, normalize the result, then check startsWith using Path components rather than a string prefix. The fixture accepts a child path and rejects a path that moves to the root's parent.",
            "Reject an absolute requested path before resolve: an absolute argument replaces the root instead of appending to it. [[java/zip-path-validation|Archive entry validation]] needs the same lexical rule before extraction."
        ]),
        ("Do not confuse a name check with an open-file guarantee", [
            "A symlink inside the root can point outside it. normalize does not inspect that target. toRealPath follows links for an existing path, but a separate check followed by an open still has a race if an attacker can change directories or links between those operations. Use a platform-aware directory-handle or secure-directory-stream design for a hostile writable tree; a lexical predicate alone is only a first filter.",
            "This teaching program returns a candidate Path and never opens it. It therefore verifies the lexical rule, not filesystem containment under adversarial mutation. [[java/atomic-file-publication|Atomic publication]] addresses a different file-operation boundary."
        ]),
    ],
    '''import java.nio.file.Path;
import java.nio.file.Paths;

public class ReceiptPathFilter {
    static Path lexicalCandidate(Path root, String requestedName) {
        Path relative = Paths.get(requestedName);
        if (relative.isAbsolute()) throw new IllegalArgumentException("absolute name");
        Path candidate = root.resolve(relative).normalize();
        if (!candidate.startsWith(root)) throw new IllegalArgumentException("outside root");
        return candidate;
    }
    public static void main(String[] args) {
        Path root = Paths.get("workspace", "receipts").toAbsolutePath().normalize();
        Path accepted = lexicalCandidate(root, "oct/../receipt-47.txt");
        System.out.println(accepted.startsWith(root));
        try { lexicalCandidate(root, "../private.txt"); }
        catch (IllegalArgumentException rejected) { System.out.println("escape rejected"); }
    }
}''',
    "true\nescape rejected",
    "Lexical normalization visits a bounded number of path components and allocates a Path representation; the precise cost is provider-dependent. No filesystem I/O occurs here. Real-path resolution and opening add I/O and a race analysis that this fixture intentionally does not claim to solve.",
    ["Do not compare path prefixes as strings; sibling names can share a textual prefix.", "Do not expect normalize to resolve a symlink or prove physical containment.", "Do not check and later open a hostile path without a race-resistant design."],
    ["java/zip-path-validation", "java/files", "java/atomic-file-publication", "java/file-channels"],
    "java-advanced",
)

for path in added:
    entry = lookup[path]
    entry["data"]["related"] = [
        {"path": related, "title": lookup[related]["title"]}
        for related in entry.pop("_related_paths")
    ]

modules = {
    "java/dsa-in-java": (
        "Node-chain algorithms and ownership",
        ["java/reverse-singly-linked-chain", "java/linked-cycle-entry", "java/merge-sorted-linked-chains", "java/linked-palindrome-restore"],
    ),
    "java/java": (
        "Array references and checked totals",
        ["java/array-copy-ownership", "java/checked-integer-arithmetic"],
    ),
    "java/advanced-java": (
        "Generic arrays, completion and path boundaries",
        ["java/generic-varargs-boundary", "java/completion-service-order", "java/threadpool-caller-runs", "java/path-lexical-boundary"],
    ),
}
for hub_path, (title, lessons) in modules.items():
    hub = lookup[hub_path]
    hub["data"]["modules"] = [item for item in hub["data"]["modules"] if item["title"] != title]
    hub["data"]["modules"].append({
        "title": title,
        "summary": "Track node ownership, failure cases and checked resource limits.",
        "lessons": lessons,
    })
    hub["updated_at"] = stamp

reverse = {
    "java/linkedlist": ["java/reverse-singly-linked-chain", "java/linked-cycle-entry"],
    "java/linkedlist-reverse-traversal": ["java/reverse-singly-linked-chain", "java/linked-palindrome-restore"],
    "java/linkedlist-exercises": ["java/merge-sorted-linked-chains", "java/linked-palindrome-restore"],
    "java/merge-sort": ["java/merge-sorted-linked-chains"],
    "java/arrays": ["java/array-copy-ownership"],
    "java/record-defensive-copy": ["java/array-copy-ownership"],
    "java/operators": ["java/checked-integer-arithmetic"],
    "java/generics": ["java/generic-varargs-boundary"],
    "java/varargs": ["java/generic-varargs-boundary"],
    "java/executors": ["java/completion-service-order", "java/threadpool-caller-runs"],
    "java/executor-rejection": ["java/threadpool-caller-runs"],
    "java/files": ["java/path-lexical-boundary"],
    "java/zip-path-validation": ["java/path-lexical-boundary"],
}
for path, targets in reverse.items():
    entry = lookup[path]
    marker = "<h2>Related node and runtime checks</h2>"
    entry["body"] = entry["body"].split(marker)[0] + marker + paragraph(
        "Continue with " + ", ".join("[[" + target + "|" + lookup[target]["title"] + "]]" for target in targets) + "."
    )
    entry["updated_at"] = stamp

FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print("Added", len(added), "Java lessons; linked from", len(reverse), "existing lessons")
