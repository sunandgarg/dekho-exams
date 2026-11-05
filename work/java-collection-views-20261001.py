"""Add original Java sequenced-collection and view-contract tutorials."""

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


def add(slug, title, definition, sections, source, output, cost, mistakes, related, release):
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
        subject="java-advanced" if release >= 21 else "java",
        category="Programming",
        tags=["java", "collections", slug],
        difficulty="Intermediate",
        sort_order=1020 + len(added),
        status="published",
        featured=False,
        published_at=stamp,
        created_at=stamp,
        updated_at=stamp,
    )
    entry["data"] = {
        "subject_root": "java/java",
        "section_path": "java/advanced-java" if release >= 21 else "java/java",
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
    "linkedlist-reversed-write-through",
    "Java 21 LinkedList.reversed: write-through order and endpoint edits",
    "LinkedList.reversed returns a reverse-ordered view whose endpoint mutations change the original list.",
    [
        ("Orient the endpoints", [
            "The first element of the reversed view is the last element of the backing list. An addFirst on that view therefore appends at the backing tail; removeLast removes the backing head. The view is not a copied sequence. Later edits to the backing list appear through the same view, and edits to the view write through.",
            "This Java 21 method differs from [[java/linkedlist-reverse-traversal|descendingIterator]], which only traverses the existing list backward. If a stable snapshot is required, copy the reversed view into a separate list and decide whether its mutable elements also need copying."
        ]),
        ("Do not infer thread safety", [
            "A view does not add synchronization. A structural edit while a second thread traverses either orientation still needs an ownership or locking rule. [[java/linkedlist-failfast-boundary|Fail-fast behavior]] is only a bug signal and cannot serve as a concurrency protocol.",
            "The reversed view retains the backing list. Keeping the view alive keeps that collection reachable. For a short-lived report, [[java/list-copyof-element-alias|copy boundaries]] may be more appropriate."
        ]),
    ],
    '''import java.util.LinkedList;

public class ReversedDispatchQueue {
    public static void main(String[] args) {
        LinkedList<String> dispatches = new LinkedList<>();
        dispatches.add("load-47");
        dispatches.add("seal-82");
        LinkedList<String> reverse = dispatches.reversed();
        reverse.addFirst("ship-15");
        System.out.println(dispatches);
        System.out.println(reverse);
        System.out.println(reverse.removeLast());
        System.out.println(dispatches);
    }
}''',
    "[load-47, seal-82, ship-15]\n[ship-15, seal-82, load-47]\nload-47\n[seal-82, ship-15]",
    "Constructing the view does not copy the list elements. Endpoint insertion and removal on LinkedList are constant-time operations; iteration over either orientation is O(n). The view and its backing list share one mutable structure.",
    ["Do not call reversed a snapshot.", "Do not read addFirst on the reversed view as insertion at the backing head.", "Do not use fail-fast exceptions as a substitute for synchronization."],
    ["java/linkedlist-reverse-traversal", "java/sequenced-collections", "java/linkedlist-failfast-boundary", "java/list-copyof-element-alias"],
    21,
)


add(
    "sequenced-list-endpoint-contract",
    "Java 21 List endpoint methods: availability is not mutability",
    "Java 21 List exposes first and last endpoint methods, but whether an endpoint can be changed still depends on the list implementation.",
    [
        ("Separate interface shape from operation support", [
            "A LinkedList supports getFirst, getLast, addFirst, and removeLast. A List created with List.of has the same endpoint method names but rejects mutation. Code accepting List<String> cannot infer modifiability from the interface alone. Decide whether the caller owns a mutable list before attempting an edit.",
            "Empty endpoints have a different failure mode: getFirst and removeLast throw NoSuchElementException on an empty list. For a queue-like contract in which absence is normal, [[java/deque-empty-contracts|Deque polling]] can express that choice, subject to its null-element policy."
        ]),
        ("Preserve the release boundary", [
            "These List endpoint methods are a Java 21 surface. A program compiled with --release 8 cannot call them even though LinkedList had similarly named methods earlier through Deque. The declared type controls which methods are visible to the compiler.",
            "[[java/linkedlist-reversed-write-through|Reversed views]] invert endpoint orientation. Test each operation against the collection contract instead of assuming an English description like first means the original head."
        ]),
    ],
    '''import java.util.LinkedList;
import java.util.List;
import java.util.NoSuchElementException;

public class DispatchListEndpoints {
    public static void main(String[] args) {
        List<String> mutable = new LinkedList<>(List.of("seal-47", "ship-82"));
        mutable.addFirst("load-15");
        System.out.println(mutable.getFirst() + ":" + mutable.getLast());
        System.out.println(mutable.removeLast());
        try { List.of("audit-20").addFirst("intake-35"); }
        catch (UnsupportedOperationException rejected) { System.out.println("immutable edit rejected"); }
        try { new LinkedList<String>().getFirst(); }
        catch (NoSuchElementException absent) { System.out.println("empty endpoint rejected"); }
    }
}''',
    "load-15:ship-82\nship-82\nimmutable edit rejected\nempty endpoint rejected",
    "The endpoint methods avoid an explicit numeric index, but their cost depends on the concrete List. LinkedList endpoints are O(1); using a generic List interface does not promise that cost or mutation support.",
    ["Do not assume List.addFirst is supported just because it compiles.", "Do not call getFirst on an empty list without an absence policy.", "Do not confuse the compile-time List type with a specific LinkedList implementation."],
    ["java/sequenced-collections", "java/linkedlist", "java/deque-empty-contracts", "java/linkedlist-reversed-write-through"],
    21,
)


add(
    "linkedhashmap-explicit-position",
    "Java 21 LinkedHashMap.putFirst and putLast for explicit key order",
    "LinkedHashMap.putFirst and putLast place a mapping at a chosen encounter-order endpoint, including when the key already exists.",
    [
        ("Separate replacement from relocation", [
            "Ordinary put on an insertion-order LinkedHashMap replaces an existing value without making that key the newest entry. putFirst and putLast explicitly move an existing mapping to the requested endpoint. The return value is the previous value for that key, or null when no previous mapping existed. Null values complicate using that return as a presence signal; containsKey answers the separate presence question.",
            "The fixture replaces a queued dispatch count while moving its key to the front, then moves another key to the back. Its output states both the value change and the final key order."
        ]),
        ("Use order as a contract", [
            "A HashMap has no encounter-order contract. If ordering is part of a response or processing policy, choose the ordered implementation deliberately. [[java/linkedhashmap|LinkedHashMap fundamentals]] cover insertion and access order; [[java/linkedhashmap-reversed-view|the reversed map view]] adds an inverse orientation in Java 21.",
            "Mutating the map while another thread iterates requires a synchronization or ownership boundary. Endpoint placement does not make the map concurrent."
        ]),
    ],
    '''import java.util.LinkedHashMap;

public class ReorderDispatchCounts {
    public static void main(String[] args) {
        LinkedHashMap<String, Integer> counts = new LinkedHashMap<>();
        counts.put("load-15", 1);
        counts.put("seal-47", 2);
        counts.put("ship-82", 3);
        System.out.println(counts.putFirst("ship-82", 4));
        counts.putLast("load-15", 1);
        System.out.println(counts.keySet());
        System.out.println(counts.get("ship-82"));
    }
}''',
    "3\n[ship-82, seal-47, load-15]\n4",
    "Explicit endpoint placement is a map operation rather than a sort. LinkedHashMap lookup and update are expected constant-time under ordinary hash distribution, while full traversal is O(n). Keys and values are retained by reference.",
    ["Do not expect put on an insertion-order map to reposition an existing key.", "Do not treat a null return as proof that the key was absent if null values are permitted.", "Do not infer thread safety from a predictable encounter order."],
    ["java/linkedhashmap", "java/linkedhashmap-reversed-view", "java/linkedhashset-endpoint-relocation", "java/sequenced-collections"],
    21,
)


add(
    "linkedhashmap-reversed-view",
    "Java 21 SequencedMap.reversed: edits through a reverse-ordered map view",
    "A reversed SequencedMap view exposes the opposite encounter order and writes supported changes into the backing map.",
    [
        ("Translate the operation", [
            "On a LinkedHashMap, putFirst through the reversed view places a mapping at the backing map's last endpoint. pollLastEntry through the view removes the backing map's first mapping. The view is not a detached map and does not duplicate key or value objects.",
            "Use the returned entry from pollLastEntry only after checking whether the map was empty. It returns null on an empty map. This fixture starts nonempty and prints the removed key to make the orientation visible."
        ]),
        ("Avoid accidental access-order changes", [
            "This program uses insertion order. An access-order LinkedHashMap has a different movement policy, and some reads can reorder it. When order drives eviction or display, specify which policy is in force and test it separately. [[java/linkedhashmap-explicit-position|Explicit positioning]] gives a narrower contract when the application chooses the endpoint.",
            "Reversed view iterators still traverse a mutable map. Concurrent structural changes need an ownership rule; [[java/linkedlist-failfast-boundary|fail-fast observation]] is not a lock."
        ]),
    ],
    '''import java.util.LinkedHashMap;
import java.util.Map;
import java.util.SequencedMap;

public class ReverseDispatchMap {
    public static void main(String[] args) {
        LinkedHashMap<String, Integer> counts = new LinkedHashMap<>();
        counts.put("load-15", 1);
        counts.put("seal-47", 2);
        SequencedMap<String, Integer> reverse = counts.reversed();
        reverse.putFirst("ship-82", 3);
        System.out.println(counts.keySet());
        System.out.println(reverse.sequencedKeySet());
        Map.Entry<String, Integer> removed = reverse.pollLastEntry();
        System.out.println(removed.getKey());
        System.out.println(counts.keySet());
    }
}''',
    "[load-15, seal-47, ship-82]\n[ship-82, seal-47, load-15]\nload-15\n[seal-47, ship-82]",
    "The reversed map is a view, so construction does not copy n mappings. Encounter-order traversal is O(n). Endpoint edits propagate to the backing LinkedHashMap; the view and original require the same mutation discipline.",
    ["Do not call reversed a defensive copy.", "Do not read pollLastEntry on a reversed view as removal of the backing tail.", "Do not dereference an empty-map poll result without checking for null."],
    ["java/linkedhashmap-explicit-position", "java/linkedhashmap", "java/sequenced-collections", "java/collections-unmodifiable-live-view"],
    21,
)


add(
    "linkedhashset-endpoint-relocation",
    "Java 21 LinkedHashSet.addFirst and addLast relocate existing elements",
    "LinkedHashSet.addFirst and addLast can move an existing member to an encounter-order endpoint without creating a duplicate.",
    [
        ("Treat membership and order separately", [
            "A Set still contains one occurrence of each equal element. The Java 21 endpoint methods can reposition that occurrence: addFirst moves a member to the front, and addLast moves it to the back. Ordinary add of an existing member does not express that relocation. This matters when a deduplicated processing queue also has a display or retry order.",
            "The fixture moves one dispatch ID forward and another backward, then removes the last. The final size checks membership separately from order. A duplicate value is not a second node."
        ]),
        ("Use a mutable implementation deliberately", [
            "SequencedSet describes encounter order but does not promise that every implementation supports repositioning. LinkedHashSet does. If the application needs key/value pairs as well, [[java/linkedhashmap-explicit-position|LinkedHashMap endpoint placement]] provides the analogous map operation.",
            "Element equality and hash codes must remain stable while stored in a hash-based set. Mutating fields used by hashCode can make a member unreachable through ordinary lookup even though iteration still shows it."
        ]),
    ],
    '''import java.util.LinkedHashSet;
import java.util.List;

public class ReorderDispatchIds {
    public static void main(String[] args) {
        LinkedHashSet<String> dispatchIds = new LinkedHashSet<>(
            List.of("load-15", "seal-47", "ship-82"));
        dispatchIds.addFirst("ship-82");
        dispatchIds.addLast("load-15");
        System.out.println(dispatchIds);
        System.out.println(dispatchIds.removeLast());
        System.out.println(dispatchIds.size());
    }
}''',
    "[ship-82, seal-47, load-15]\nload-15\n2",
    "Repositioning does not allocate a second entry for an existing member. Hash-based membership operations are expected constant-time under ordinary hash distribution; iterating the order remains O(n).",
    ["Do not expect two copies of the same set member after relocation.", "Do not assume every SequencedSet implementation supports endpoint mutation.", "Do not mutate fields used in an element's equality or hash code while it is in a hash set."],
    ["java/linkedhashmap-explicit-position", "java/linkedhashmap", "java/sequenced-collections", "java/immutable-collections"],
    21,
)


add(
    "deque-reversed-orientation",
    "Java 21 Deque.reversed: translate head and tail mutations",
    "Deque.reversed supplies a reverse-ordered deque view, so its head is the backing deque's tail.",
    [
        ("Read operations from the view's orientation", [
            "Adding at the view's front appends at the backing deque's end. Polling the view's last element removes the backing deque's first. This translation is visible with ArrayDeque and does not require copying every queued item.",
            "A queue consumer may expect pollFirst to mean oldest work. Passing it a reversed view changes that meaning. Name the orientation at an API boundary instead of accepting an arbitrary Deque and assuming the head is always the intake side."
        ]),
        ("Retain the container's element rules", [
            "ArrayDeque forbids null elements. That keeps a null poll result usable as an empty signal. [[java/linkedlist-null-head|LinkedList can contain null]], so the same signal is ambiguous there. A reversed view inherits the underlying deque's element and concurrency constraints; it does not sanitize them.",
            "For a read-only backward pass through LinkedList, [[java/linkedlist-reverse-traversal|descendingIterator]] is enough. Use a reversed Deque when the caller intentionally needs the inverse endpoint operations."
        ]),
    ],
    '''import java.util.ArrayDeque;
import java.util.Deque;

public class ReverseDispatchDeque {
    public static void main(String[] args) {
        Deque<String> dispatches = new ArrayDeque<>();
        dispatches.addLast("load-15");
        dispatches.addLast("seal-47");
        Deque<String> reverse = dispatches.reversed();
        reverse.addFirst("ship-82");
        System.out.println(dispatches);
        System.out.println(reverse.pollLast());
        System.out.println(dispatches);
    }
}''',
    "[load-15, seal-47, ship-82]\nload-15\n[seal-47, ship-82]",
    "The reversed view avoids copying the deque. ArrayDeque endpoint operations are amortized O(1), while traversal is O(n). The view shares all elements and mutation state with its backing deque.",
    ["Do not treat a reversed deque head as the original intake head.", "Do not insert null into ArrayDeque.", "Do not assume a view is an independently synchronized queue."],
    ["java/arraydeque", "java/deque-empty-contracts", "java/linkedlist-reversed-write-through", "java/linkedlist-null-head"],
    21,
)


add(
    "arrays-aslist-backed-view",
    "Arrays.asList in Java: fixed-size list backed by the original array",
    "Arrays.asList creates a fixed-size List view over an array, so element replacement is shared in both directions.",
    [
        ("Separate size from value mutation", [
            "The list permits set, and that write changes the array slot. Updating the array slot also changes what the list reads. Structural operations such as add or remove are unsupported because the underlying array length cannot change. The view retains the array; neither side is a snapshot.",
            "The generic varargs signature has a trap with primitive arrays: Arrays.asList(int[]) produces a one-element List<int[]> rather than boxing each integer. For boxed integers, use Integer[] or an explicit stream/loop conversion."
        ]),
        ("Make the copy boundary explicit", [
            "When a caller needs an independent mutable list, construct an ArrayList from this view. That copies element references, not mutable element objects. [[java/list-copyof-element-alias|List.copyOf]] instead gives an unmodifiable container snapshot, while [[java/collections-unmodifiable-live-view|unmodifiableList]] stays backed by its source.",
            "Passing the view across ownership boundaries lets later array edits change the recipient's observations. Treat that shared backing as part of the API contract."
        ]),
    ],
    '''import java.util.Arrays;
import java.util.List;

public class ArrayBackedDispatchList {
    public static void main(String[] args) {
        String[] dispatchIds = {"load-15", "seal-47"};
        List<String> view = Arrays.asList(dispatchIds);
        view.set(0, "load-82");
        System.out.println(dispatchIds[0]);
        dispatchIds[1] = "seal-35";
        System.out.println(view);
        try { view.add("ship-20"); }
        catch (UnsupportedOperationException rejected) { System.out.println("size change rejected"); }
        int[] primitiveKeys = {47, 82};
        System.out.println(Arrays.asList(primitiveKeys).size());
    }
}''',
    "load-82\n[load-82, seal-35]\nsize change rejected\n1",
    "Creating the view does not copy the array and uses a small wrapper allocation. Indexed reads and replacements are O(1). Copying into a separate list costs O(n) references and still does not clone referenced objects.",
    ["Do not call Arrays.asList a resizable ArrayList.", "Do not expect primitive array elements to become separate boxed list members.", "Do not hand off the view if later array edits must be invisible."],
    ["java/arrays", "java/arraylist", "java/list-copyof-element-alias", "java/collections-unmodifiable-live-view"],
    8,
)


add(
    "collections-unmodifiable-live-view",
    "Collections.unmodifiableList is a live view, not a snapshot",
    "Collections.unmodifiableList rejects mutation through the wrapper but reflects changes made through its backing list.",
    [
        ("Block one path, not every alias", [
            "The wrapper's add and remove methods throw UnsupportedOperationException. A code path that still owns the mutable source can append, and the wrapper then exposes the appended element. This is read-only access through one reference, not immutability of the underlying state.",
            "If an API must freeze the container membership at handoff time, [[java/list-copyof-element-alias|List.copyOf]] takes an unmodifiable container snapshot. It still retains references to mutable elements. Stronger isolation requires a policy for those elements too."
        ]),
        ("Protect traversal when sharing across threads", [
            "An unmodifiable view does not synchronize its source. A writer on the backing LinkedList can invalidate a reader's traversal. [[java/synchronized-list-iteration|Synchronized wrappers]] require a specific locking discipline, and a private snapshot can avoid shared mutation when its copying cost is acceptable.",
            "The wrapper also retains the backing list. Holding the wrapper for a long time keeps that backing collection and its elements reachable."
        ]),
    ],
    '''import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class LiveDispatchReadOnlyView {
    public static void main(String[] args) {
        List<String> mutable = new ArrayList<>();
        mutable.add("load-15");
        List<String> readOnly = Collections.unmodifiableList(mutable);
        mutable.add("seal-47");
        System.out.println(readOnly);
        try { readOnly.add("ship-82"); }
        catch (UnsupportedOperationException rejected) { System.out.println("wrapper edit rejected"); }
        System.out.println(mutable.size());
    }
}''',
    "[load-15, seal-47]\nwrapper edit rejected\n2",
    "Wrapping does not copy n elements. Reads delegate to the backing list, so their cost follows its implementation. The wrapper and source share one mutable container and all referenced element objects.",
    ["Do not describe an unmodifiable view as a frozen snapshot.", "Do not keep a mutable backing alias if the consumer requires stable membership.", "Do not infer thread safety from the word unmodifiable."],
    ["java/list-copyof-element-alias", "java/arrays-aslist-backed-view", "java/synchronized-list-iteration", "java/immutable-collections"],
    8,
)


add(
    "list-copyof-element-alias",
    "List.copyOf freezes container membership but not mutable elements",
    "List.copyOf returns an unmodifiable list with the source collection's elements at copy time, while retaining references to those elements.",
    [
        ("Separate container snapshot from object snapshot", [
            "Appending a new shipment record to the source list does not append it to the copied list. Mutating a ShipmentRecord already present changes the status observed through both lists because both hold the same object. This distinction matters for cached responses, audit trails, and cross-thread handoffs.",
            "Null elements are rejected. A copy operation can also avoid a fresh allocation when its input is already an unmodifiable list, so code must not rely on a distinct list identity. Its content contract matters more than whether the returned reference is new."
        ]),
        ("Choose the needed isolation level", [
            "For an independent mutable container, use a new ArrayList. For immutable record values, a shallow container copy may be enough. For mutable nested objects, create purpose-built value snapshots before List.copyOf. [[java/record-defensive-copy|Record defensive copies]] address a related boundary for array fields.",
            "[[java/collections-unmodifiable-live-view|Collections.unmodifiableList]] leaves membership live through the backing collection. These two APIs solve different ownership problems despite both rejecting edits through the returned reference."
        ]),
    ],
    '''import java.util.ArrayList;
import java.util.List;

public class DispatchContainerSnapshot {
    static final class ShipmentRecord {
        final String dispatchId;
        String status;
        ShipmentRecord(String dispatchId, String status) {
            this.dispatchId = dispatchId; this.status = status;
        }
    }
    public static void main(String[] args) {
        ShipmentRecord first = new ShipmentRecord("load-15", "queued");
        List<ShipmentRecord> source = new ArrayList<>();
        source.add(first);
        List<ShipmentRecord> snapshot = List.copyOf(source);
        source.add(new ShipmentRecord("seal-47", "queued"));
        first.status = "sent";
        System.out.println(snapshot.size());
        System.out.println(snapshot.get(0).status);
        try { List.copyOf(java.util.Arrays.asList("ship-82", null)); }
        catch (NullPointerException rejected) { System.out.println("null rejected"); }
    }
}''',
    "1\nsent\nnull rejected",
    "Copying n element references costs O(n) traversal and generally O(n) container storage, though an implementation may reuse a suitable immutable input. Mutable element objects are shared; copying the container alone does not isolate their state.",
    ["Do not call a shallow container snapshot a deep copy.", "Do not assume List.copyOf accepts null elements.", "Do not rely on a fresh returned object identity."],
    ["java/collections-unmodifiable-live-view", "java/array-copy-ownership", "java/record-defensive-copy", "java/arrays-aslist-backed-view"],
    10,
)


add(
    "linkedhashmap-access-order-reversal",
    "Java 21 access-order LinkedHashMap: reads change a reversed view",
    "An access-order LinkedHashMap moves a successfully accessed mapping toward its backing tail, so a reversed view reports that mapping first.",
    [
        ("Make the ordering policy visible", [
            "The third LinkedHashMap constructor argument selects access order. A successful get changes encounter order even though no mapping is inserted or removed. If a reverse-ordered view is already held, its first key can change after that read. A renderer that assumes reads are observational can produce different output after a cache lookup.",
            "The fixture prints both orientations before and after accessing the oldest key. The mapping count stays fixed. The order change comes from the chosen map policy, not from copying or rebuilding the reverse view."
        ]),
        ("Separate explicit placement from access", [
            "[[java/linkedhashmap-explicit-position|putFirst and putLast]] reposition an entry because the caller requested an endpoint. Access order repositions an entry as a side effect of operations such as get. Use one policy deliberately; a cache and a stable report have different needs.",
            "Iteration over either view while another thread accesses the map needs a concurrency rule. Access-order movement can count as structural change for iterator behavior, so [[java/linkedlist-failfast-boundary|fail-fast exceptions]] remain diagnostics rather than coordination."
        ]),
    ],
    '''import java.util.LinkedHashMap;
import java.util.SequencedMap;

public class AccessOrderedDispatchCache {
    public static void main(String[] args) {
        LinkedHashMap<String, Integer> cache = new LinkedHashMap<>(16, 0.75f, true);
        cache.put("load-15", 1);
        cache.put("seal-47", 2);
        cache.put("ship-82", 3);
        SequencedMap<String, Integer> reverse = cache.reversed();
        System.out.println(reverse.sequencedKeySet());
        System.out.println(cache.get("load-15"));
        System.out.println(cache.keySet());
        System.out.println(reverse.sequencedKeySet());
    }
}''',
    "[ship-82, seal-47, load-15]\n1\n[seal-47, ship-82, load-15]\n[load-15, ship-82, seal-47]",
    "The view does not copy map entries. A successful lookup is expected constant-time under ordinary hash distribution but also changes ordering in this map mode. Traversing either orientation is O(n), and both references share the same mutable mappings.",
    ["Do not assume get leaves an access-order map's iteration order unchanged.", "Do not treat a reversed view as a frozen cache report.", "Do not rely on fail-fast iteration to make concurrent access safe."],
    ["java/linkedhashmap", "java/linkedhashmap-reversed-view", "java/linkedhashmap-explicit-position", "java/linkedlist-failfast-boundary"],
    21,
)


for path in added:
    entry = lookup[path]
    entry["data"]["related"] = [
        {"path": related, "title": lookup[related]["title"]}
        for related in entry.pop("_related_paths")
    ]

modules = {
    "java/advanced-java": (
        "Java 21 sequenced collection views",
        ["java/linkedlist-reversed-write-through", "java/sequenced-list-endpoint-contract", "java/linkedhashmap-explicit-position", "java/linkedhashmap-reversed-view", "java/linkedhashset-endpoint-relocation", "java/deque-reversed-orientation", "java/linkedhashmap-access-order-reversal"],
    ),
    "java/java": (
        "Collection backing and snapshots",
        ["java/arrays-aslist-backed-view", "java/collections-unmodifiable-live-view", "java/list-copyof-element-alias"],
    ),
}
for hub_path, (title, lessons) in modules.items():
    hub = lookup[hub_path]
    hub["data"]["modules"] = [item for item in hub["data"]["modules"] if item["title"] != title]
    hub["data"]["modules"].append({
        "title": title,
        "summary": "Track encounter order, write-through views, copies, and mutation ownership.",
        "lessons": lessons,
    })
    hub["updated_at"] = stamp

reverse = {
    "java/linkedlist": ["java/linkedlist-reversed-write-through", "java/sequenced-list-endpoint-contract"],
    "java/linkedlist-reverse-traversal": ["java/linkedlist-reversed-write-through", "java/deque-reversed-orientation"],
    "java/linkedlist-failfast-boundary": ["java/linkedlist-reversed-write-through", "java/linkedhashmap-access-order-reversal"],
    "java/sequenced-collections": ["java/sequenced-list-endpoint-contract", "java/linkedhashmap-reversed-view", "java/linkedhashset-endpoint-relocation"],
    "java/linkedhashmap": ["java/linkedhashmap-explicit-position", "java/linkedhashmap-reversed-view", "java/linkedhashmap-access-order-reversal"],
    "java/arraydeque": ["java/deque-reversed-orientation"],
    "java/deque-empty-contracts": ["java/sequenced-list-endpoint-contract", "java/deque-reversed-orientation"],
    "java/arrays": ["java/arrays-aslist-backed-view", "java/list-copyof-element-alias"],
    "java/arraylist": ["java/arrays-aslist-backed-view", "java/collections-unmodifiable-live-view"],
    "java/immutable-collections": ["java/collections-unmodifiable-live-view", "java/list-copyof-element-alias"],
    "java/record-defensive-copy": ["java/list-copyof-element-alias"],
    "java/synchronized-list-iteration": ["java/collections-unmodifiable-live-view", "java/list-copyof-element-alias"],
}
for path, targets in reverse.items():
    entry = lookup[path]
    marker = "<h2>Collection views and copy boundaries</h2>"
    entry["body"] = entry["body"].split(marker)[0] + marker + paragraph(
        "Continue with " + ", ".join("[[" + target + "|" + lookup[target]["title"] + "]]" for target in targets) + "."
    )
    entry["updated_at"] = stamp

FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print("Added", len(added), "Java lessons; linked from", len(reverse), "existing lessons")
