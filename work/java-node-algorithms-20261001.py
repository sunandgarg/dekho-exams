"""Publish original Java node-chain algorithm lessons and reciprocal links."""

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


def add(slug, title, definition, sections, source, output, cost, mistakes, related):
    path = "java/" + slug
    body = paragraph(definition)
    for heading, paragraphs in sections:
        body += "<h2>" + heading + "</h2>" + "".join(paragraph(item) for item in paragraphs)
    body += "<h2>Working program</h2>" + block(source)
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
        subject="java-dsa",
        category="Programming",
        tags=["java", "linked-list", slug],
        difficulty="Intermediate",
        sort_order=980 + len(added),
        status="published",
        featured=False,
        published_at=stamp,
        created_at=stamp,
        updated_at=stamp,
    )
    entry["data"] = {
        "subject_root": "java/java",
        "section_path": "java/dsa-in-java",
        "kind": "tutorial",
        "content_format": "html",
        "reading_minutes": max(4, round(len(re.sub("<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial",
        "related": [],
        "seo_ready": True,
        "java_release": 8,
        "java_version": "8+",
    }
    entry["_related_paths"] = related
    if path in lookup:
        entries[entries.index(lookup[path])] = entry
    else:
        entries.append(entry)
    lookup[path] = entry
    added.append(path)


add(
    "linked-remove-nth-from-end",
    "Remove the nth node from the end of a Java linked chain",
    "Removing the nth node from the end requires a gap of n links between two cursors, then one link replacement at the predecessor.",
    [
        ("Reject an invalid position before mutation", [
            "Use a sentinel before the head so deletion of the first real node follows the same rule as deletion in the middle. Advance the leading cursor n links from the sentinel. If it reaches null too early, n exceeds the chain length. Zero and negative positions are not meaningful and must fail before any link changes.",
            "Keep the cursor gap fixed while the leading cursor still has a successor. The trailing cursor then stops at the predecessor of the target. Save the target, bypass it, and clear its next reference so code that still holds the removed node cannot walk into the live chain."
        ]),
        ("State the ownership boundary", [
            "This operation mutates an application-owned acyclic Node chain. It is not a way to obtain internal nodes from [[java/linkedlist|java.util.LinkedList]]. If a caller retains aliases into the original chain, those aliases still point to the same objects; only the root and predecessor links change. Run [[java/linked-cycle-entry|cycle detection]] first if the input can contain a cycle.",
            "A successful deletion returns the possibly new head. Ignoring that return value loses a head deletion. For value-based removal through the collection API, use [[java/linkedlist-occurrences|LinkedList occurrence removal]] instead."
        ]),
    ],
    '''public class RemoveDispatchFromTail {
    static final class Node {
        final String dispatchId;
        Node next;
        Node(String dispatchId, Node next) { this.dispatchId = dispatchId; this.next = next; }
    }
    static Node remove(Node head, int positionFromEnd) {
        if (positionFromEnd <= 0) throw new IllegalArgumentException("position must be positive");
        Node sentinel = new Node("sentinel", head);
        Node lead = sentinel;
        for (int step = 0; step < positionFromEnd; step++) {
            if (lead.next == null) throw new IllegalArgumentException("position exceeds length");
            lead = lead.next;
        }
        Node before = sentinel;
        while (lead.next != null) { lead = lead.next; before = before.next; }
        Node removed = before.next;
        before.next = removed.next;
        removed.next = null;
        return sentinel.next;
    }
    static String labels(Node head) {
        StringBuilder result = new StringBuilder();
        for (Node cursor = head; cursor != null; cursor = cursor.next) {
            if (result.length() > 0) result.append(",");
            result.append(cursor.dispatchId);
        }
        return result.toString();
    }
    public static void main(String[] args) {
        Node head = new Node("load-47", new Node("seal-82", new Node("ship-15", null)));
        head = remove(head, 3);
        System.out.println(labels(head));
        head = remove(head, 1);
        System.out.println(labels(head));
        try { remove(head, 2); }
        catch (IllegalArgumentException rejected) { System.out.println("invalid position rejected"); }
    }
}''',
    "seal-82,ship-15\nseal-82\ninvalid position rejected",
    "One traversal takes O(n) time and O(1) extra references. The sentinel is one temporary node allocation. This method assumes exclusive mutation of the chain; concurrent readers need a separate publication or synchronization rule.",
    ["Do not treat n as a zero-based offset.", "Do not ignore the returned head when the first node can be removed.", "Do not advance both cursors before checking whether the requested position exists."],
    ["java/linked-cycle-entry", "java/linked-stable-partition", "java/linkedlist-occurrences", "java/linked-algorithm-invariants"],
)


add(
    "linked-stable-partition",
    "Stable partition of a singly linked chain in Java",
    "A stable linked-chain partition relinks existing nodes into two groups while preserving their original order within each group.",
    [
        ("Detach before appending", [
            "Maintain one tail for records below the threshold and another for the rest. Take a node from the input, save its original successor, then set its next to null before appending it to one group. Detachment prevents an old successor from silently linking the groups or leaving a cycle when the two tails are joined.",
            "For this fixture, priorities below 50 go first. The records with priorities 70 and 55 keep their mutual order, as do 20 and 35. A sort would change more than the partition contract and usually need extra comparisons."
        ]),
        ("Avoid hidden input assumptions", [
            "The input must be acyclic and privately owned for mutation. A null head is valid and returns null. Reusing an input node from another chain creates aliasing between the two owners; establish a single owner or copy the nodes first. [[java/linked-intersection-identity|Intersection by identity]] can detect a shared tail before destructive operations.",
            "This differs from the collection's [[java/linkedlist-stable-sort|stable sort]]: sorting orders every pair, while a partition only classifies against a threshold."
        ]),
    ],
    '''public class PartitionDispatchPriority {
    static final class Node {
        final String dispatchId;
        final int priority;
        Node next;
        Node(String dispatchId, int priority, Node next) {
            this.dispatchId = dispatchId; this.priority = priority; this.next = next;
        }
    }
    static Node partition(Node head, int threshold) {
        Node earlyRoot = new Node("early", 0, null);
        Node laterRoot = new Node("later", 0, null);
        Node earlyTail = earlyRoot, laterTail = laterRoot;
        for (Node cursor = head; cursor != null;) {
            Node following = cursor.next;
            cursor.next = null;
            if (cursor.priority < threshold) { earlyTail.next = cursor; earlyTail = cursor; }
            else { laterTail.next = cursor; laterTail = cursor; }
            cursor = following;
        }
        earlyTail.next = laterRoot.next;
        return earlyRoot.next;
    }
    static String labels(Node head) {
        StringBuilder result = new StringBuilder();
        for (Node cursor = head; cursor != null; cursor = cursor.next) {
            if (result.length() > 0) result.append(",");
            result.append(cursor.dispatchId);
        }
        return result.toString();
    }
    public static void main(String[] args) {
        Node head = new Node("review-70", 70,
            new Node("ship-20", 20, new Node("hold-55", 55, new Node("pack-35", 35, null))));
        System.out.println(labels(partition(head, 50)));
        System.out.println(partition(null, 50) == null);
    }
}''',
    "ship-20,pack-35,review-70,hold-55\ntrue",
    "Each node moves through one cursor step, so the operation takes O(n) time and O(1) extra references plus two sentinel nodes. It does not clone payload objects. The two temporary sentinels are not part of the returned chain.",
    ["Do not append a node without clearing its stale next reference.", "Do not promise global sorting from a two-group partition.", "Do not mutate an aliased chain while another owner traverses it."],
    ["java/linked-intersection-identity", "java/linked-merge-sort-stability", "java/merge-sorted-linked-chains", "java/linkedlist-stable-sort"],
)


add(
    "linked-intersection-identity",
    "Find the shared node of two Java linked chains by identity",
    "Two singly linked chains intersect only when they reach the same Node object, not when their payload strings happen to match.",
    [
        ("Align the remaining lengths", [
            "Count each acyclic chain once. Advance the cursor of the longer chain by the difference in lengths, then move both cursors together until their references are identical or both reach null. Shared nodes form a common suffix because one Node has only one next link.",
            "A payload comparison can report a false intersection. Two dispatch records may carry the same identifier and still live in separate node objects. The second fixture makes that distinction visible."
        ]),
        ("Handle cycles separately", [
            "Length counting cannot terminate on a cycle. If the chains are not known to be acyclic, first use [[java/linked-cycle-entry|cycle-entry detection]] and define what intersection means for cyclic inputs. This lesson deliberately solves the simpler acyclic contract.",
            "Intersection is an ownership warning before [[java/linked-stable-partition|partitioning]] or [[java/merge-sorted-linked-chains|merging]] by relinking nodes. If two roots share a tail, changing one root's links can change the other root's traversal."
        ]),
    ],
    '''public class SharedDispatchTail {
    static final class Node {
        final String dispatchId;
        Node next;
        Node(String dispatchId, Node next) { this.dispatchId = dispatchId; this.next = next; }
    }
    static int length(Node head) {
        int count = 0;
        for (Node cursor = head; cursor != null; cursor = cursor.next) count++;
        return count;
    }
    static Node intersection(Node first, Node second) {
        int firstLength = length(first), secondLength = length(second);
        while (firstLength > secondLength) { first = first.next; firstLength--; }
        while (secondLength > firstLength) { second = second.next; secondLength--; }
        while (first != second) { first = first.next; second = second.next; }
        return first;
    }
    public static void main(String[] args) {
        Node shared = new Node("dispatch-47", new Node("ship-82", null));
        Node intake = new Node("load-15", shared);
        Node audit = new Node("verify-35", new Node("hold-20", shared));
        System.out.println(intersection(intake, audit).dispatchId);
        Node separate = new Node("dispatch-47", null);
        System.out.println(intersection(intake, separate) == null);
    }
}''',
    "dispatch-47\ntrue",
    "Counting and alignment visit at most O(a+b) nodes and use O(1) extra references. No hash set is needed. The result is a borrowed Node reference; callers must not infer sole ownership from finding it.",
    ["Do not use value equality to detect structural intersection.", "Do not run the length pass on an unverified cyclic chain.", "Do not destructively merge roots that already share a suffix."],
    ["java/linked-cycle-entry", "java/linked-stable-partition", "java/merge-sorted-linked-chains", "java/linked-random-pointer-copy"],
)


add(
    "linked-deduplicate-sorted",
    "Remove repeated keys from a sorted Java linked chain",
    "Deduplicating a sorted linked chain can keep the first node for each key by bypassing adjacent nodes with equal keys.",
    [
        ("Use the ordering precondition", [
            "Equal keys must be adjacent. Compare each node with its successor; when keys match, bypass the successor and clear that removed node's next reference. Keep the cursor on the retained node because a run may contain more than two copies. Advance only after the next key differs.",
            "This policy keeps the first record of a duplicate run. If the product instead requires the latest record or rejects all duplicates, the algorithm and its output contract must change. The linked chain itself does not enforce sorted order."
        ]),
        ("Separate keys from node identity", [
            "The fixture uses numeric shipment keys rather than comparing Node references. Two records with key 47 are distinct nodes, but one is removed under this value-based policy. [[java/linked-intersection-identity|Intersection detection]] asks a different question: whether two paths reach the same object.",
            "If input order is uncertain, sort first with [[java/linked-merge-sort-stability|linked merge sort]] or use a set with its corresponding memory cost. A single adjacent comparison is insufficient on unsorted input."
        ]),
    ],
    '''public class SortedShipmentDeduplication {
    static final class Node {
        final int shipmentKey;
        Node next;
        Node(int shipmentKey, Node next) { this.shipmentKey = shipmentKey; this.next = next; }
    }
    static Node keepFirstPerKey(Node head) {
        for (Node cursor = head; cursor != null && cursor.next != null;) {
            if (cursor.shipmentKey == cursor.next.shipmentKey) {
                Node removed = cursor.next;
                cursor.next = removed.next;
                removed.next = null;
            } else cursor = cursor.next;
        }
        return head;
    }
    static String keys(Node head) {
        StringBuilder result = new StringBuilder();
        for (Node cursor = head; cursor != null; cursor = cursor.next) {
            if (result.length() > 0) result.append(",");
            result.append(cursor.shipmentKey);
        }
        return result.toString();
    }
    public static void main(String[] args) {
        Node head = new Node(15, new Node(15, new Node(47,
            new Node(47, new Node(47, new Node(82, null))))));
        System.out.println(keys(keepFirstPerKey(head)));
        System.out.println(keepFirstPerKey(null) == null);
    }
}''',
    "15,47,82\ntrue",
    "One pass costs O(n) time and O(1) extra references. The operation mutates the original chain and retains the first Node object of each equal-key run; it does not copy records.",
    ["Do not apply adjacent deduplication to unsorted input.", "Do not advance the cursor immediately after removing one duplicate; a run may continue.", "Do not equate duplicate key values with shared Node identity."],
    ["java/linked-merge-sort-stability", "java/linked-intersection-identity", "java/linkedlist-retainall-equality", "java/linked-stable-partition"],
)


add(
    "linked-rotate-right",
    "Rotate a singly linked chain right by k positions in Java",
    "A right rotation moves the final k nodes of an acyclic singly linked chain to the front without copying them.",
    [
        ("Reduce the shift before changing links", [
            "Measure the chain length and retain its tail. A shift by the length, or any multiple of it, changes nothing, so use k modulo length. For a nonzero remainder, the new tail is length minus remainder minus one links from the old head. Join the old tail to the old head only after those positions are known, then cut the new tail's next link.",
            "Reject negative shifts as a separate contract rather than silently interpreting them as left rotations. Empty and single-node chains return unchanged. This avoids division by zero and unnecessary temporary cycles."
        ]),
        ("Publish the returned root", [
            "Rotation changes which node is first. The caller must replace its root with the returned reference; an alias to the old head now points into the middle. This is the same root-ownership issue as [[java/reverse-singly-linked-chain|reversal]], though neither operation copies payloads.",
            "A cycle in the input would make length measurement nonterminating. Use [[java/linked-cycle-entry|cycle detection]] if acyclicity is not established when building the chain."
        ]),
    ],
    '''public class RotateDispatchChain {
    static final class Node {
        final String dispatchId;
        Node next;
        Node(String dispatchId, Node next) { this.dispatchId = dispatchId; this.next = next; }
    }
    static Node rotateRight(Node head, int positions) {
        if (positions < 0) throw new IllegalArgumentException("negative rotation");
        if (head == null || head.next == null) return head;
        int length = 1;
        Node tail = head;
        while (tail.next != null) { tail = tail.next; length++; }
        int shift = positions % length;
        if (shift == 0) return head;
        Node newTail = head;
        for (int step = 1; step < length - shift; step++) newTail = newTail.next;
        Node newHead = newTail.next;
        tail.next = head;
        newTail.next = null;
        return newHead;
    }
    static String labels(Node head) {
        StringBuilder result = new StringBuilder();
        for (Node cursor = head; cursor != null; cursor = cursor.next) {
            if (result.length() > 0) result.append(",");
            result.append(cursor.dispatchId);
        }
        return result.toString();
    }
    public static void main(String[] args) {
        Node head = new Node("load-15", new Node("seal-47", new Node("ship-82", null)));
        System.out.println(labels(rotateRight(head, 5)));
        System.out.println(rotateRight(null, 47) == null);
    }
}''',
    "seal-47,ship-82,load-15\ntrue",
    "Length measurement and the split walk take O(n) time with O(1) extra references. The temporary cycle exists only between two assignments within this method; concurrent traversal or exceptions inserted between them would require a stronger synchronization design.",
    ["Do not connect tail to head before determining the cut point.", "Do not use the old head after publishing the rotated root.", "Do not calculate modulo length when the chain is empty."],
    ["java/reverse-singly-linked-chain", "java/linked-middle-split", "java/linked-cycle-entry", "java/linked-reverse-k-group"],
)


add(
    "linked-merge-sort-stability",
    "Stable merge sort for a singly linked chain in Java",
    "Linked merge sort repeatedly splits an acyclic chain and merges sorted halves, choosing the left node first when keys tie.",
    [
        ("Split without indexed access", [
            "A slow cursor moves one link and a fast cursor moves two. Starting fast at head.next leaves the extra node on the left when the length is odd. Cut slow.next before recursing; without that cut, the left recursion still points into the right half and never reaches a smaller input.",
            "Merge by relinking existing nodes. The comparison uses less than or equal so equal-priority records from the left half remain before equal-priority records from the right half. That is the stability contract; changing it to strict less than can reverse ties across halves."
        ]),
        ("Budget stack and ownership", [
            "This top-down version uses recursion depth O(log n) for splitting, unlike [[java/linked-reverse-k-group|in-place group reversal]]. It does not allocate a second array or clone payload objects. Java's [[java/linkedlist-stable-sort|List.sort contract]] is a different API surface; this implementation exists for code that owns Node references.",
            "Shared suffixes and cycles violate the independent-chain precondition. Detect [[java/linked-intersection-identity|shared tails]] or [[java/linked-cycle-entry|cycles]] before sorting untrusted node graphs."
        ]),
    ],
    '''public class SortDispatchChain {
    static final class Node {
        final String dispatchId;
        final int priority;
        Node next;
        Node(String dispatchId, int priority, Node next) {
            this.dispatchId = dispatchId; this.priority = priority; this.next = next;
        }
    }
    static Node sort(Node head) {
        if (head == null || head.next == null) return head;
        Node slow = head, fast = head.next;
        while (fast != null && fast.next != null) { slow = slow.next; fast = fast.next.next; }
        Node right = slow.next;
        slow.next = null;
        return merge(sort(head), sort(right));
    }
    static Node merge(Node left, Node right) {
        Node sentinel = new Node("sentinel", 0, null), tail = sentinel;
        while (left != null && right != null) {
            if (left.priority <= right.priority) { tail.next = left; left = left.next; }
            else { tail.next = right; right = right.next; }
            tail = tail.next;
        }
        tail.next = left != null ? left : right;
        return sentinel.next;
    }
    static String labels(Node head) {
        StringBuilder result = new StringBuilder();
        for (Node cursor = head; cursor != null; cursor = cursor.next) {
            if (result.length() > 0) result.append(",");
            result.append(cursor.dispatchId);
        }
        return result.toString();
    }
    public static void main(String[] args) {
        Node head = new Node("review-47", 47, new Node("ship-15", 15,
            new Node("hold-47", 47, new Node("pack-20", 20, null))));
        System.out.println(labels(sort(head)));
        System.out.println(sort(null) == null);
    }
}''',
    "ship-15,pack-20,review-47,hold-47\ntrue",
    "Splitting and merging take O(n log n) time. Recursive call frames use O(log n) space; each merge allocates one short-lived sentinel, with O(n) such allocations over the full sort. Nodes and payloads are reused, so the returned root replaces the old one.",
    ["Do not leave the halves connected before recursion.", "Do not choose the right node on equal keys if stable order matters.", "Do not claim O(1) total auxiliary memory for this recursive implementation."],
    ["java/merge-sorted-linked-chains", "java/linked-deduplicate-sorted", "java/linked-stable-partition", "java/linkedlist-stable-sort"],
)


add(
    "linked-random-pointer-copy",
    "Copy a Java linked chain with random references without retaining aliases",
    "Copying a linked chain with random references requires a new Node for every original and a mapping from original identity to copied identity.",
    [
        ("Allocate before wiring", [
            "Walk the next chain once to allocate copies. A second walk assigns next and random links through an IdentityHashMap. Identity matters: two nodes may have the same label, and equals may have domain behavior unrelated to graph topology. Random links can point backward or forward, so wiring during a single allocation pass can encounter a target not yet copied.",
            "The program rejects a random target outside the next chain. Silently mapping that reference to null would corrupt the copied graph. A different product may need to copy an entire reachable graph instead; that requires graph traversal and an explicit policy for cycles and external objects."
        ]),
        ("Separate shallow and structural copies", [
            "[[java/linkedlist-shallow-copy|LinkedList.clone]] copies collection structure but still refers to the same elements. Here each Node object is new while its immutable label string can be shared safely. If payloads were mutable, a full independent copy would also require a payload-copy policy.",
            "The next chain must be acyclic for these two linear walks. Check [[java/linked-cycle-entry|cycle entry]] before copying if upstream construction does not enforce it."
        ]),
    ],
    '''import java.util.IdentityHashMap;

public class CopyDispatchReferences {
    static final class Node {
        final String dispatchId;
        Node next;
        Node random;
        Node(String dispatchId) { this.dispatchId = dispatchId; }
    }
    static Node copy(Node head) {
        IdentityHashMap<Node, Node> copies = new IdentityHashMap<>();
        for (Node cursor = head; cursor != null; cursor = cursor.next)
            copies.put(cursor, new Node(cursor.dispatchId));
        for (Node cursor = head; cursor != null; cursor = cursor.next) {
            Node replica = copies.get(cursor);
            replica.next = copies.get(cursor.next);
            if (cursor.random != null && !copies.containsKey(cursor.random))
                throw new IllegalArgumentException("random target outside chain");
            replica.random = copies.get(cursor.random);
        }
        return copies.get(head);
    }
    public static void main(String[] args) {
        Node intake = new Node("intake-47");
        Node audit = new Node("audit-82");
        intake.next = audit;
        intake.random = audit;
        audit.random = intake;
        Node replica = copy(intake);
        System.out.println(replica != intake && replica.next != audit);
        System.out.println(replica.random == replica.next);
        System.out.println(replica.next.random == replica);
    }
}''',
    "true\ntrue\ntrue",
    "Two next-chain passes take O(n) time. The identity map and copied nodes use O(n) extra memory. The original chain is not mutated; only the immutable label values are reused.",
    ["Do not key the copy map by payload value when distinct nodes may share a label.", "Do not silently erase a random edge whose target lies outside the defined input chain.", "Do not describe a node copy as a deep copy of mutable payload objects."],
    ["java/linked-intersection-identity", "java/linked-cycle-entry", "java/linkedlist-shallow-copy", "java/array-copy-ownership"],
)


add(
    "linked-reverse-k-group",
    "Reverse complete groups of k nodes in a Java linked chain",
    "Group reversal changes links within each complete run of k nodes and leaves a shorter final run in its original order.",
    [
        ("Find the boundary before mutation", [
            "Starting from a sentinel before the current group, walk k links to locate its last node. If there are fewer than k nodes, stop before changing any link in that partial group. Save the node after the group, then reverse links until that saved boundary is reached.",
            "After reversal, the old group head is the new tail. Connect the previous group's tail to the former last node and advance the group predecessor to the former head. Both links matter: skipping either can discard a suffix or form a cycle."
        ]),
        ("Define k and input ownership", [
            "Reject k less than one. A group size of one returns the same topology, while an empty chain stays empty. The method assumes an acyclic, exclusively mutable Node chain; it cannot operate on private nodes inside [[java/linkedlist|java.util.LinkedList]].",
            "If the requirement is to reverse the entire chain, [[java/reverse-singly-linked-chain|whole-chain reversal]] is smaller. If it is to move a suffix to the front without reversing its order, use [[java/linked-rotate-right|rotation]]."
        ]),
    ],
    '''public class ReverseDispatchGroups {
    static final class Node {
        final String dispatchId;
        Node next;
        Node(String dispatchId, Node next) { this.dispatchId = dispatchId; this.next = next; }
    }
    static Node reverseGroups(Node head, int groupSize) {
        if (groupSize <= 0) throw new IllegalArgumentException("group size must be positive");
        Node sentinel = new Node("sentinel", head), before = sentinel;
        while (true) {
            Node last = before;
            for (int step = 0; step < groupSize && last != null; step++) last = last.next;
            if (last == null) return sentinel.next;
            Node after = last.next;
            Node cursor = before.next, previous = after;
            while (cursor != after) {
                Node following = cursor.next;
                cursor.next = previous;
                previous = cursor;
                cursor = following;
            }
            Node oldHead = before.next;
            before.next = last;
            before = oldHead;
        }
    }
    static String labels(Node head) {
        StringBuilder result = new StringBuilder();
        for (Node cursor = head; cursor != null; cursor = cursor.next) {
            if (result.length() > 0) result.append(",");
            result.append(cursor.dispatchId);
        }
        return result.toString();
    }
    public static void main(String[] args) {
        Node head = new Node("load-15", new Node("seal-47", new Node("scan-82",
            new Node("pack-20", new Node("ship-35", null)))));
        System.out.println(labels(reverseGroups(head, 2)));
        System.out.println(reverseGroups(null, 3) == null);
    }
}''',
    "seal-47,load-15,pack-20,scan-82,ship-35\ntrue",
    "Each node participates in a constant number of scans and link writes, giving O(n) time and O(1) extra references. One sentinel is allocated. Existing Node identities and payload objects are preserved.",
    ["Do not reverse a final group smaller than k when the contract says complete groups only.", "Do not forget to reconnect the previous group to its new head.", "Do not allow k equal to zero; the boundary scan would make no progress."],
    ["java/reverse-singly-linked-chain", "java/linked-rotate-right", "java/linked-middle-split", "java/linked-algorithm-invariants"],
)


add(
    "linked-middle-split",
    "Split a Java linked chain into two halves without copying nodes",
    "A slow and a fast cursor can split an acyclic linked chain into a left half and a right half by clearing one next link.",
    [
        ("Choose where the odd node belongs", [
            "Start the fast cursor one link ahead of the slow cursor. When the fast cursor reaches the end, slow is the final node of the left half. For odd lengths, the left half gets the extra node. Save slow.next as the right root, then set slow.next to null to make two independent chains.",
            "For an empty chain, return two null roots. For one node, return that node on the left and null on the right. These cases must be explicit before dereferencing head.next."
        ]),
        ("Treat split as a mutation", [
            "The original head now reaches only the left half. A caller that needs both must retain the returned pair. This is the same cut required by [[java/linked-merge-sort-stability|linked merge sort]] before recursing. Without it, recursion can revisit the same nodes indefinitely.",
            "The method assumes no cycle and no concurrent traversal. If another root shares a suffix, splitting can alter that root's traversal too; check [[java/linked-intersection-identity|intersection by identity]] when ownership is uncertain."
        ]),
    ],
    '''public class SplitDispatchChain {
    static final class Node {
        final String dispatchId;
        Node next;
        Node(String dispatchId, Node next) { this.dispatchId = dispatchId; this.next = next; }
    }
    static Node[] split(Node head) {
        if (head == null) return new Node[] {null, null};
        Node slow = head, fast = head.next;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
        }
        Node right = slow.next;
        slow.next = null;
        return new Node[] {head, right};
    }
    static String labels(Node head) {
        StringBuilder result = new StringBuilder();
        for (Node cursor = head; cursor != null; cursor = cursor.next) {
            if (result.length() > 0) result.append(",");
            result.append(cursor.dispatchId);
        }
        return result.toString();
    }
    public static void main(String[] args) {
        Node head = new Node("load-15", new Node("scan-47", new Node("seal-82",
            new Node("pack-20", new Node("ship-35", null)))));
        Node[] halves = split(head);
        System.out.println(labels(halves[0]));
        System.out.println(labels(halves[1]));
        System.out.println(split(null)[1] == null);
    }
}''',
    "load-15,scan-47,seal-82\npack-20,ship-35\ntrue",
    "The two-cursor walk takes O(n) time and O(1) cursor space; the returned two-element array is a fixed allocation. No Node or payload is copied, and both returned roots own existing links.",
    ["Do not forget the cut at slow.next.", "Do not dereference head.next before handling an empty input.", "Do not assume both halves have equal length for odd-sized chains."],
    ["java/linked-merge-sort-stability", "java/linked-rotate-right", "java/linked-intersection-identity", "java/linked-cycle-entry"],
)


add(
    "linked-algorithm-invariants",
    "Test Java linked-chain mutations with node-identity invariants",
    "A linked-chain mutation test should check node identity, topology, and termination, not only the printed sequence of payloads.",
    [
        ("Check topology after each operation", [
            "A reversal can print the expected labels while allocating replacement nodes, dropping a duplicate-valued node, or leaving a hidden cycle. Construct chains from distinct Node objects, reverse them, and traverse with an IdentityHashMap so a repeated object is rejected before a test loop can hang. Compare each visited reference with the expected original object.",
            "This fixture enumerates lengths zero through eight, reverses each chain twice, and checks that both passes contain exactly the original nodes in the expected order. The empty and one-node cases matter; they expose root handling that a three-node demonstration can miss."
        ]),
        ("Know what the fixture does not prove", [
            "Nine shapes do not prove correctness for all inputs, nor do they test concurrent mutation or cycles supplied as input. Add larger randomized inputs and independent oracles for release checks. The article demonstrates a focused invariant test for [[java/reverse-singly-linked-chain|whole-chain reversal]], then points to [[java/linked-reverse-k-group|group reversal]] and [[java/linked-remove-nth-from-end|deletion]] for separate contracts.",
            "A step cap protects test execution from a regression that forms a cycle. It is a test guard, not an algorithmic property of the production function."
        ]),
    ],
    '''import java.util.IdentityHashMap;

public class DispatchChainInvariantCheck {
    static final class Node {
        final int dispatchKey;
        Node next;
        Node(int dispatchKey) { this.dispatchKey = dispatchKey; }
    }
    static Node reverse(Node head) {
        Node previous = null;
        for (Node cursor = head; cursor != null;) {
            Node following = cursor.next;
            cursor.next = previous;
            previous = cursor;
            cursor = following;
        }
        return previous;
    }
    static void assertOrder(Node head, Node[] expected, boolean reversed) {
        IdentityHashMap<Node, Boolean> visited = new IdentityHashMap<>();
        Node cursor = head;
        for (int offset = 0; offset < expected.length; offset++) {
            int expectedIndex = reversed ? expected.length - 1 - offset : offset;
            if (cursor != expected[expectedIndex] || visited.put(cursor, true) != null)
                throw new AssertionError("identity or order changed");
            cursor = cursor.next;
        }
        if (cursor != null) throw new AssertionError("extra node or cycle");
    }
    public static void main(String[] args) {
        for (int size = 0; size <= 8; size++) {
            Node[] original = new Node[size];
            for (int index = 0; index < size; index++) original[index] = new Node(47 + index);
            for (int index = 1; index < size; index++) original[index - 1].next = original[index];
            Node root = size == 0 ? null : original[0];
            Node reversed = reverse(root);
            assertOrder(reversed, original, true);
            assertOrder(reverse(reversed), original, false);
        }
        System.out.println("9 chain lengths checked");
    }
}''',
    "9 chain lengths checked",
    "Each fixture of n nodes uses O(n) time for construction and each traversal, plus O(n) references in the expected array and identity map. Across the nine fixed lengths, total work is bounded. The production reverse function itself still uses O(1) extra references.",
    ["Do not use value equality to prove original nodes were retained.", "Do not let a test traverse a possibly cyclic result without an identity guard or step bound.", "Do not treat a small enumeration as proof of every input contract."],
    ["java/reverse-singly-linked-chain", "java/linked-reverse-k-group", "java/linked-remove-nth-from-end", "java/linked-cycle-entry"],
)


for path in added:
    entry = lookup[path]
    entry["data"]["related"] = [
        {"path": related, "title": lookup[related]["title"]}
        for related in entry.pop("_related_paths")
    ]

hub = lookup["java/dsa-in-java"]
module_title = "Linked-chain mutation, sorting and identity"
hub["data"]["modules"] = [item for item in hub["data"]["modules"] if item["title"] != module_title]
hub["data"]["modules"].append({
    "title": module_title,
    "summary": "Relink owned nodes, preserve identity, and test the resulting topology.",
    "lessons": added,
})
hub["updated_at"] = stamp

reverse = {
    "java/reverse-singly-linked-chain": ["java/linked-reverse-k-group", "java/linked-algorithm-invariants"],
    "java/linked-cycle-entry": ["java/linked-remove-nth-from-end", "java/linked-intersection-identity"],
    "java/merge-sorted-linked-chains": ["java/linked-merge-sort-stability", "java/linked-stable-partition"],
    "java/linked-palindrome-restore": ["java/linked-middle-split", "java/linked-algorithm-invariants"],
    "java/linkedlist": ["java/linked-remove-nth-from-end", "java/linked-stable-partition"],
    "java/linkedlist-exercises": ["java/linked-reverse-k-group", "java/linked-deduplicate-sorted"],
    "java/linkedlist-interview": ["java/linked-intersection-identity", "java/linked-random-pointer-copy"],
    "java/linkedlist-examples": ["java/linked-rotate-right", "java/linked-middle-split"],
    "java/linkedlist-stable-sort": ["java/linked-merge-sort-stability"],
    "java/linkedlist-shallow-copy": ["java/linked-random-pointer-copy"],
    "java/linkedlist-occurrences": ["java/linked-remove-nth-from-end", "java/linked-deduplicate-sorted"],
    "java/merge-sort": ["java/linked-merge-sort-stability"],
    "java/two-pointers": ["java/linked-intersection-identity", "java/linked-middle-split"],
}
for path, targets in reverse.items():
    entry = lookup[path]
    marker = "<h2>Continue with owned-node algorithms</h2>"
    entry["body"] = entry["body"].split(marker)[0] + marker + paragraph(
        "Continue with " + ", ".join("[[" + target + "|" + lookup[target]["title"] + "]]" for target in targets) + "."
    )
    entry["updated_at"] = stamp

FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print("Added", len(added), "Java lessons; linked from", len(reverse), "existing lessons")
