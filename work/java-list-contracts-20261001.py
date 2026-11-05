"""Add original Java collection adapter and mutation-contract lessons."""

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
    if path in lookup:
        raise ValueError("Existing path: " + path)
    body = paragraph(definition)
    for heading, paragraphs in sections:
        body += "<h2>" + heading + "</h2>" + "".join(paragraph(item) for item in paragraphs)
    body += "<h2>Working program</h2>" + block(source)
    body += "<h3>Output</h3>" + block(output, "text")
    body += "<h2>Cost and ownership</h2>" + paragraph(cost)
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in mistakes) + "</ul>"
    body += "<h2>Read next</h2>" + paragraph(
        ", ".join("[[" + target + "|" + lookup.get(target, {}).get("title", target.rsplit("/", 1)[-1].replace("-", " ")) + "]]" for target in related) + "."
    )
    entry = copy.deepcopy(lookup["java/casts"])
    entry.update(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
        path=path,
        title=title,
        summary=definition,
        body=body,
        subject="java-advanced",
        category="Programming",
        tags=["java", "collections", slug],
        difficulty="Intermediate",
        sort_order=1300 + len(added),
        status="published",
        featured=False,
        published_at=stamp,
        created_at=stamp,
        updated_at=stamp,
    )
    entry["data"] = {
        "subject_root": "java/java",
        "section_path": "java/advanced-java",
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
    entries.append(entry)
    lookup[path] = entry
    added.append(path)


add(
    "linkedlist-synchronized-iteration",
    "Java synchronized LinkedList iteration: hold the wrapper lock for the whole scan",
    "Collections.synchronizedList serializes individual calls, but a multi-step iteration still needs an external lock on the returned wrapper.",
    [
        ("Protect the whole observation", [
            "An audit worker cannot safely assume that a synchronized size call and a later iterator traversal describe one queue state. Another writer can modify the list between those operations. Acquire the wrapper monitor before creating and consuming the iterator when the scan must be consistent with cooperating writers.",
            "The fixture uses one thread to show the correct lock boundary. It does not claim that a deterministic single-thread run proves concurrency safety. [[java/linkedlist-failfast-boundary|Fail-fast behavior]] is a bug signal, not the synchronization mechanism."
        ]),
        ("Keep the backing list private", [
            "The wrapper works only when every participant uses the wrapper or the same monitor. If a caller retains and mutates the raw LinkedList directly, the wrapper cannot protect that path. A long scan also blocks writers, so take an intentional snapshot under the lock when later processing is slow."
        ]),
    ],
    '''import java.util.*;

public class AuditQueueSnapshot {
    public static void main(String[] args) {
        List<String> auditQueue = Collections.synchronizedList(new LinkedList<String>());
        auditQueue.add("receipt-47");
        auditQueue.add("receipt-82");
        List<String> snapshot;
        synchronized (auditQueue) {
            snapshot = new ArrayList<String>(auditQueue);
        }
        System.out.println(snapshot);
    }
}''',
    "[receipt-47, receipt-82]",
    "Copying n elements takes O(n) time and memory while holding the wrapper lock. Process the independent snapshot after releasing it; returning an iterator over the live list would carry the synchronization duty to the caller.",
    ["Do not assume a synchronized wrapper makes an iterator automatically safe.", "Do not lock the original backing list while writers lock only the wrapper.", "Do not run slow remote work under the collection monitor."],
    ["java/linkedlist", "java/linkedlist-failfast-boundary", "java/collection-views", "java/locks"],
)


add(
    "linkedlist-remove-overload",
    "Java LinkedList<Integer>.remove: index and value choose different overloads",
    "LinkedList.remove(int) removes at a position, whereas remove(Object) removes the first equal element.",
    [
        ("Make the target explicit", [
            "An Integer list has two plausible meanings for remove(1). The primitive int chooses the positional overload, so the second element disappears even when its value is not one. Box the value deliberately when a business identifier must be removed by equality.",
            "The fixture removes the element at position one, then removes a separate value. [[java/linkedlist-occurrences|Occurrence removal]] covers first and last equal values; [[java/linkedlist-indexed-scan|indexed traversal]] explains the search cost behind positional access."
        ]),
        ("Handle absence without guessing", [
            "remove(Object) returns false when no equal element exists. remove(int) throws for an invalid position. Those failure shapes should not be collapsed into the same recovery path in an API adapter."
        ]),
    ],
    '''import java.util.*;

public class DispatchIdRemoval {
    public static void main(String[] args) {
        LinkedList<Integer> dispatchIds = new LinkedList<Integer>(Arrays.asList(17, 23, 47));
        System.out.println("position=" + dispatchIds.remove(1));
        System.out.println("value=" + dispatchIds.remove(Integer.valueOf(47)));
        System.out.println(dispatchIds);
    }
}''',
    "position=23\nvalue=true\n[17]",
    "Both positional and equality-based removal may traverse O(n) nodes; unlinking a located node is constant structural work. Do not infer that a LinkedList makes arbitrary indexed deletion constant-time from the node unlink alone.",
    ["Do not pass an int when the intended target is an Integer value.", "Do not confuse false for an absent value with IndexOutOfBoundsException for an absent index.", "Do not assume removing an arbitrary index is O(1)."],
    ["java/linkedlist", "java/linkedlist-occurrences", "java/linkedlist-indexed-scan", "java/arraylist"],
)


add(
    "list-replaceall-partial-failure",
    "Java List.replaceAll: a thrown operator can leave earlier elements changed",
    "List.replaceAll applies an operator across elements without promising an all-or-nothing update if that operator throws.",
    [
        ("Validate before writing", [
            "A batch normalizer may accept the first record and reject a later malformed one. At that point the list can contain both transformed and original values. If the whole queue must change atomically, calculate a separate candidate list, validate every result, then replace the owned reference under the application's publication rule.",
            "The fixture makes the failure deterministic at the second element. It shows the resulting mixed list on the tested LinkedList implementation; callers should rely on the absence of an atomicity promise, not on which prefix an arbitrary implementation will have updated."
        ]),
        ("Separate element and list ownership", [
            "Even a copied list shares element objects unless the elements themselves are copied. This example uses immutable strings, so the candidate values are independent. [[java/linkedlist-shallow-copy|Shallow copying]] matters when a replacement operator mutates the contained objects instead."
        ]),
    ],
    '''import java.util.*;

public class BatchCodeNormalization {
    public static void main(String[] args) {
        LinkedList<String> batchCodes = new LinkedList<String>(Arrays.asList("r-17", "invalid", "r-47"));
        try {
            batchCodes.replaceAll(code -> {
                if (code.equals("invalid")) throw new IllegalArgumentException("bad code");
                return code.toUpperCase(Locale.ROOT);
            });
        } catch (IllegalArgumentException rejected) {
            System.out.println("batch rejected");
        }
        System.out.println(batchCodes);
    }
}''',
    "batch rejected\n[R-17, invalid, r-47]",
    "The scan is O(n) and creates a replacement string for each accepted element. Building a candidate list costs O(n) additional references but allows validation before publication. A mutation of shared element objects needs a deeper ownership policy.",
    ["Do not treat replaceAll as a transaction.", "Do not publish a partially transformed list after an operator throws.", "Do not assume copying a list clones its contained objects."],
    ["java/linkedlist", "java/linkedlist-shallow-copy", "java/collection-views", "java/iterators"],
)


add(
    "collections-copy-destination-size",
    "Java Collections.copy: the destination must already have slots",
    "Collections.copy replaces existing destination elements; it does not grow an empty list to fit the source.",
    [
        ("Allocate positions before copying", [
            "An empty LinkedList has capacity to grow but has no elements to overwrite. Collections.copy requires destination.size() to be at least source.size(). An adapter that expects insertion will fail before producing a backup copy.",
            "The fixture first shows the failure on an empty destination, then creates three placeholder positions and copies the source. A constructor copy such as new ArrayList(source) is simpler when no existing destination must be reused."
        ]),
        ("Know what was copied", [
            "Only element references are copied. A mutable object in the source remains shared with the destination, and extra destination elements remain in place. [[java/linkedlist-shallow-copy|LinkedList shallow copying]] shows the same element-ownership boundary."
        ]),
    ],
    '''import java.util.*;

public class DispatchBackupSlots {
    public static void main(String[] args) {
        List<String> source = Arrays.asList("D-17", "D-23", "D-47");
        LinkedList<String> backup = new LinkedList<String>();
        try { Collections.copy(backup, source); }
        catch (IndexOutOfBoundsException rejected) { System.out.println("slots missing"); }
        backup.addAll(Arrays.asList("reserved", "reserved", "reserved"));
        Collections.copy(backup, source);
        System.out.println(backup);
    }
}''',
    "slots missing\n[D-17, D-23, D-47]",
    "Copying n references takes O(n) time. This implementation allocates destination nodes before the copy and therefore O(n) additional list storage. The operation does not deep-copy mutable records or provide transactional publication.",
    ["Do not expect Collections.copy to append into an empty list.", "Do not assume a copied reference is an independent mutable object.", "Do not forget that destination elements beyond source length remain unchanged."],
    ["java/linkedlist-shallow-copy", "java/collection-views", "java/linkedlist", "java/arraylist"],
)


add(
    "collections-rotate-sublist",
    "Java Collections.rotate on a subList: change only a live window",
    "Collections.rotate changes element order within the supplied List, and a subList argument writes through to its parent list.",
    [
        ("Bound the reordering region", [
            "A dispatch schedule may allow a three-slot shift while keeping the opening and closing duties fixed. Passing schedule.subList(1, 4) rotates only the middle window. The parent list changes because the subList is a view, not a detached copy.",
            "The fixture moves the last middle duty to the start of that window. [[java/linkedlist-sublist-view|Sublist ownership]] explains why callers holding the parent see the update. Do not mutate the parent structurally while relying on a retained sublist view."
        ]),
        ("Do not confuse rotation with moving nodes", [
            "The API promises the resulting order, not a particular node-relinking algorithm. On a linked list, the implementation may exchange element references or use a temporary array. Choose the operation because its semantics fit, not because you expect a specific internal shortcut."
        ]),
    ],
    '''import java.util.*;

public class DutyWindowRotation {
    public static void main(String[] args) {
        LinkedList<String> duties = new LinkedList<String>(Arrays.asList("open", "scan", "pack", "seal", "close"));
        Collections.rotate(duties.subList(1, 4), 1);
        System.out.println(duties);
    }
}''',
    "[open, seal, scan, pack, close]",
    "Rotation of a window of k elements costs at least O(k) element visits and may use implementation-specific temporary storage. The subList itself is a view; it does not allocate a second independent schedule.",
    ["Do not expect subList to isolate the parent from mutations.", "Do not assume rotation physically relinks LinkedList nodes.", "Do not keep a subList across unrelated structural edits to its parent."],
    ["java/linkedlist-sublist-view", "java/linkedlist", "java/collections-unmodifiable-live-view", "java/sorting"],
)


add(
    "collections-lifo-queue-deque",
    "Java Collections.asLifoQueue: a Queue view with stack ordering",
    "Collections.asLifoQueue exposes a Deque through Queue methods while inserting and removing at its front.",
    [
        ("Read the adapter's order", [
            "A caller may see a Queue type and assume first-in, first-out behavior. This adapter deliberately provides last-in, first-out order: the second added task is removed first. The view and backing deque share contents, so a mutation through either reference is immediately visible through the other.",
            "The fixture uses LinkedList as the backing deque so the order is easy to inspect. For a non-null stack workload, [[java/arraydeque|ArrayDeque]] is often a better starting point; choose based on the actual null and memory contracts."
        ]),
        ("Keep the view private when ordering matters", [
            "Code with direct access to the underlying deque can add at either end and defeat the ordering assumptions of clients holding only the Queue view. Encapsulate both references behind one application API if task order is a correctness rule."
        ]),
    ],
    '''import java.util.*;

public class UrgentTaskStackView {
    public static void main(String[] args) {
        Deque<String> taskDeque = new LinkedList<String>();
        Queue<String> urgentTasks = Collections.asLifoQueue(taskDeque);
        urgentTasks.add("batch-17");
        urgentTasks.add("batch-47");
        System.out.println(urgentTasks.remove());
        System.out.println(taskDeque);
    }
}''',
    "batch-47\n[batch-17]",
    "Endpoint operations on this LinkedList-backed view use constant structural work per call, while each node occupies separate storage. The view adds no independent queue; both references own access to the same mutable state.",
    ["Do not infer FIFO ordering solely from the Queue interface.", "Do not treat the view as an independent copy.", "Do not expose the backing deque when external endpoint writes would violate ordering."],
    ["java/linkedlist", "java/arraydeque", "java/deque-empty-contracts", "java/collection-views"],
)


add(
    "collections-ncopies-alias",
    "Java Collections.nCopies: repeated slots can share one mutable object",
    "Collections.nCopies produces an immutable-size list whose positions all refer to the same supplied object.",
    [
        ("Distinguish repeated values from independent records", [
            "A test fixture that needs three independent mutable notes cannot get them by repeating one StringBuilder. Mutating the object through any slot changes the text visible at every slot. The list rejects replacement operations, but it does not freeze the object itself.",
            "The program prints one reference-identity check and the resulting repeated notes. [[java/linkedlist-shallow-copy|Shallow copies]] have the same nested-object hazard even though their node storage is independent."
        ]),
        ("Choose a factory for independent objects", [
            "Construct separate elements in a loop when each slot owns mutable state. For immutable values such as String or a value record, sharing one reference is usually harmless. The contract is about object identity, not the visual similarity of printed values."
        ]),
    ],
    '''import java.util.*;

public class RepeatedReviewNote {
    public static void main(String[] args) {
        List<StringBuilder> notes = Collections.nCopies(3, new StringBuilder("open"));
        System.out.println(notes.get(0) == notes.get(2));
        notes.get(1).append("-review");
        System.out.println(notes);
    }
}''',
    "true\n[open-review, open-review, open-review]",
    "The list representation can use constant storage for the repeated reference, but creating independent mutable elements would require O(n) objects. A read at an index is constant work; the shared object's mutation cost depends on that object.",
    ["Do not use nCopies for independent mutable records.", "Do not confuse an unmodifiable list with immutable elements.", "Do not rely on equal printed values as evidence of separate identities."],
    ["java/linkedlist-shallow-copy", "java/immutable-collections", "java/collection-views", "java/linkedlist"],
)


add(
    "linkedlist-spliterator-binding",
    "Java LinkedList spliterator: traversal binds after creation",
    "LinkedList.spliterator is late-binding, so a change before its first traversal or size query can become part of the traversal.",
    [
        ("Place the binding boundary", [
            "Creating a spliterator is not necessarily a snapshot. In this fixture, a receipt added before traversal appears in the output. After a size query binds a second spliterator, a structural edit invalidates its expected state and the tested JDK reports ConcurrentModificationException.",
            "The fail-fast exception is best-effort, not a synchronization protocol. [[java/linkedlist-synchronized-iteration|Synchronized iteration]] covers ownership of a scan; [[java/spliterator-contracts|Spliterator characteristics]] explains which traversal properties may be advertised."
        ]),
        ("Choose snapshot semantics explicitly", [
            "If a parallel computation must process one stable version, copy the list under the appropriate lock before traversing. A late-binding spliterator only narrows the timing window; it does not make concurrent writers safe or define an immutable view."
        ]),
    ],
    '''import java.util.*;

public class ReceiptSpliteratorBoundary {
    public static void main(String[] args) {
        LinkedList<String> receipts = new LinkedList<String>();
        receipts.add("R-17");
        Spliterator<String> pending = receipts.spliterator();
        receipts.add("R-47");
        pending.forEachRemaining(System.out::println);

        Spliterator<String> bound = receipts.spliterator();
        bound.estimateSize();
        receipts.add("R-82");
        try { bound.forEachRemaining(receipt -> { }); }
        catch (ConcurrentModificationException changed) { System.out.println("bound scan invalidated"); }
    }
}''',
    "R-17\nR-47\nbound scan invalidated",
    "A full traversal visits O(n) elements. Splitting may buffer elements and consume additional memory; a plain sequential pass does not turn the list into a snapshot. The performance and failure boundary depend on when binding occurs.",
    ["Do not assume spliterator creation copies the list.", "Do not use a fail-fast exception as a concurrency guarantee.", "Do not mutate the backing list during a supposedly stable scan."],
    ["java/spliterator-contracts", "java/linkedlist-failfast-boundary", "java/linkedlist-synchronized-iteration", "java/linkedlist"],
)


for path in added:
    entry = lookup[path]
    entry["data"]["related"] = [{"path": target, "title": lookup[target]["title"]} for target in entry.pop("_related_paths")]

hub = lookup["java/java"]
title = "List adapters and mutation boundaries"
hub["data"]["modules"] = [module for module in hub["data"]["modules"] if module["title"] != title]
hub["data"]["modules"].append({
    "title": title,
    "summary": "Track view ownership, failure states, and copy costs before sharing or changing a Java list.",
    "lessons": added,
})
hub["updated_at"] = stamp

reverse = {
    "java/linkedlist": ["java/linkedlist-synchronized-iteration", "java/linkedlist-remove-overload", "java/linkedlist-spliterator-binding"],
    "java/collection-views": ["java/collections-lifo-queue-deque", "java/collections-ncopies-alias", "java/collections-copy-destination-size"],
    "java/linkedlist-sublist-view": ["java/collections-rotate-sublist"],
    "java/linkedlist-failfast-boundary": ["java/linkedlist-synchronized-iteration", "java/linkedlist-spliterator-binding"],
    "java/linkedlist-shallow-copy": ["java/collections-copy-destination-size", "java/collections-ncopies-alias", "java/list-replaceall-partial-failure"],
}
for path, targets in reverse.items():
    entry = lookup[path]
    marker = "<h2>List adapters and mutation boundaries</h2>"
    entry["body"] = entry["body"].split(marker)[0] + marker + paragraph(
        "Continue with " + ", ".join("[[" + target + "|" + lookup[target]["title"] + "]]" for target in targets) + "."
    )
    entry["updated_at"] = stamp

FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print("Added", len(added), "Java lessons; linked from", len(reverse), "existing lessons")
