"""Add original Java 8 stream and collector contract tutorials."""

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
        raise ValueError(path)
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
        path=path, title=title, summary=definition, body=body,
        subject="java-advanced", category="Programming", tags=["java", "streams", slug],
        difficulty="Advanced", sort_order=1450 + len(added), status="published",
        featured=False, published_at=stamp, created_at=stamp, updated_at=stamp,
    )
    entry["data"] = {
        "subject_root": "java/java", "section_path": "java/advanced-java",
        "kind": "tutorial", "content_format": "html",
        "reading_minutes": max(4, round(len(re.sub("<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial", "related": [], "seo_ready": True,
        "java_release": 8, "java_version": "8+",
    }
    entry["_related_paths"] = related
    entries.append(entry)
    lookup[path] = entry
    added.append(path)


add(
    "stream-single-use",
    "Java streams are single-use: create a new pipeline for each pass",
    "A Stream is a traversal plan, not a reusable container; obtain a fresh stream for each terminal operation.",
    [
        ("Keep the source, not the spent pipeline", [
            "A report may need both a total and a list of rejected invoices. Retain the collection that owns the data, then request a new stream for each calculation. Calling a second terminal operation on the old stream is invalid, even when its source has not changed.",
            "This matters for database-backed or file-backed sources too: a supplier can build a new pipeline, but it cannot resurrect a consumed cursor. Resource ownership still follows [[java/stream-resource-lifetime|the source lifetime]].",
        ]),
        ("Use a supplier when pipeline assembly is repeated", [
            "The supplier below creates a fresh pipeline over the same in-memory list. It captures the list, so a later mutation would affect later traversals. Copy or snapshot the source if the two results must describe one fixed state. [[java/streams|Stream fundamentals]] covers lazy execution.",
        ]),
    ],
    '''import java.util.Arrays;
import java.util.List;
import java.util.function.Supplier;
import java.util.stream.Stream;

public class InvoiceStreamPasses {
    public static void main(String[] args) {
        List<Integer> invoiceCents = Arrays.asList(4700, -300, 1250);
        Supplier<Stream<Integer>> amounts = () -> invoiceCents.stream();
        long accepted = amounts.get().filter(cents -> cents >= 0).count();
        int total = amounts.get().filter(cents -> cents >= 0)
                .mapToInt(Integer::intValue).sum();
        System.out.println("accepted=" + accepted);
        System.out.println("totalCents=" + total);
    }
}''',
    "accepted=2\ntotalCents=5950",
    "Each pass is O(n) time over the list; the supplier and pipeline add little state, but a second pass repeats traversal and any mapper work. Materialize an intermediate result only when that extra memory is cheaper than recomputation or when a fixed snapshot is required.",
    ["Do not cache a Stream field for later terminal operations.", "Do not assume a supplier makes a one-shot I/O cursor reusable.", "Do not run related calculations over a mutable source without defining snapshot semantics."],
    ["java/streams", "java/stream-resource-lifetime", "java/stream-short-circuit", "java/collectors-tomap-duplicate-key"],
)

add(
    "stream-peek-side-effects",
    "Java Stream.peek: observation is not a correctness hook",
    "peek can observe elements that a terminal operation traverses, but its action is not a reliable place for required work.",
    [
        ("Traversal determines whether the action runs", [
            "An intermediate pipeline is lazy. Creating it does not send audit events, update counters or write records. Even after a terminal call, an implementation may skip stages when it can compute the result without visiting elements. For example, count on a sized source may bypass a peek action.",
            "The program uses collect to force traversal for this particular result. Put required audit writes in an explicit loop or an owned service boundary instead of relying on peek. [[java/stream-short-circuit|Short-circuit operations]] have another reason to visit only a prefix.",
        ]),
        ("Separate inspection from mutation", [
            "A diagnostic print may help during local inspection, but it changes observable output and can become expensive in a large pipeline. [[java/lambdas|Lambda capture]] does not turn shared mutable counters into safe parallel reductions; collect a value instead.",
        ]),
    ],
    '''import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public class ShipmentPeekBoundary {
    public static void main(String[] args) {
        Stream<String> pending = Arrays.asList("PK-47", "PK-82").stream()
                .peek(packageId -> System.out.println("visited=" + packageId));
        System.out.println("pipeline-built");
        List<String> packageIds = pending.collect(Collectors.toList());
        System.out.println("collected=" + packageIds.size());
    }
}''',
    "pipeline-built\nvisited=PK-47\nvisited=PK-82\ncollected=2",
    "This traversal is O(n) time and the collected list is O(n) space. Logging adds I/O cost for each visited element; parallel execution can interleave messages and must not be used to guarantee audit order.",
    ["Do not rely on peek for required writes or validation.", "Do not assume count will execute every peek action.", "Do not use a shared mutable counter inside a parallel pipeline."],
    ["java/streams", "java/stream-short-circuit", "java/stream-parallel-encounter-order", "java/lambdas"],
)

add(
    "collectors-tomap-duplicate-key",
    "Java Collectors.toMap: choose a duplicate-key rule",
    "Collectors.toMap needs an explicit merge function when distinct input records can produce the same map key.",
    [
        ("Name the conflict policy", [
            "Two shipment updates can share an order ID. The two-argument collector throws when that happens; this is often useful during validation, but it is not a merge strategy. A merge function must state whether the earliest update, latest update or a combined value wins.",
            "This program keeps the larger revision number. That policy is independent of input order for unequal revisions, unlike a last-write-wins lambda that depends on encounter order. If equal revisions carry different payloads, reject the conflict instead of silently picking one. [[java/hashmap|Map key contracts]] still apply.",
        ]),
        ("Avoid pretending the default map is ordered", [
            "This example looks up keys directly and prints explicit fields. The basic toMap overload does not promise the map implementation or iteration order. Use [[java/collectors-tomap-order|an explicit map supplier]] when presentation order is part of the result.",
        ]),
    ],
    '''import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

public class ShipmentRevisionIndex {
    static final class Revision {
        final String orderId;
        final int number;
        Revision(String orderId, int number) {
            this.orderId = orderId;
            this.number = number;
        }
    }
    public static void main(String[] args) {
        List<Revision> updates = Arrays.asList(
                new Revision("ORD-47", 2), new Revision("ORD-82", 1),
                new Revision("ORD-47", 4));
        Map<String, Revision> newest = updates.stream().collect(Collectors.toMap(
                revision -> revision.orderId,
                revision -> revision,
                (left, right) -> left.number >= right.number ? left : right));
        System.out.println("ORD-47=" + newest.get("ORD-47").number);
        System.out.println("orders=" + newest.size());
    }
}''',
    "ORD-47=4\norders=2",
    "Collection is O(n) expected time with a hash map and O(k) space for k distinct order IDs; collision-heavy keys can change practical costs. A merge function may run multiple times for the same key, particularly in parallel collection, so it must be associative for parallel use and free of external side effects.",
    ["Do not use two-argument toMap when duplicate keys are valid input.", "Do not use a nonassociative merge policy in parallel collection.", "Do not infer iteration order from a basic toMap result."],
    ["java/hashmap", "java/collectors-tomap-order", "java/collectors-groupingby-null-key", "java/streams"],
)

add(
    "collectors-groupingby-null-key",
    "Java Collectors.groupingBy: reject or normalize null classifier keys",
    "groupingBy does not accept a null value from its classifier; define an explicit bucket before collecting nullable records.",
    [
        ("Make missing classification visible", [
            "A warehouse record without a region is not automatically part of a null-key group. The standard groupingBy collector rejects a null classifier result. Treat the missing field as invalid input, or map it to a named bucket with a clear reporting meaning.",
            "The program uses UNASSIGNED for a known reporting bucket. That is a business choice, not a library default. If the bucket could collide with a real region code, use a typed key instead of a string sentinel. [[java/optional|Optional]] can model absence before a boundary chooses its representation.",
        ]),
        ("Keep grouping costs explicit", [
            "Grouping stores references to the original records in lists. Mutating those records later changes what a reader sees through the groups; copy immutable values when the report must be a snapshot. The resulting map also has no promised iteration order.",
        ]),
    ],
    '''import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

public class WarehouseRegionBuckets {
    static final class Dispatch {
        final String id;
        final String region;
        Dispatch(String id, String region) {
            this.id = id;
            this.region = region;
        }
    }
    public static void main(String[] args) {
        List<Dispatch> dispatches = Arrays.asList(
                new Dispatch("DSP-47", "WEST"),
                new Dispatch("DSP-82", null),
                new Dispatch("DSP-91", "WEST"));
        Map<String, List<Dispatch>> byRegion = dispatches.stream().collect(
                Collectors.groupingBy(dispatch ->
                        dispatch.region == null ? "UNASSIGNED" : dispatch.region));
        System.out.println("WEST=" + byRegion.get("WEST").size());
        System.out.println("UNASSIGNED=" + byRegion.get("UNASSIGNED").get(0).id);
    }
}''',
    "WEST=2\nUNASSIGNED=DSP-82",
    "Expected grouping time is O(n) and storage is O(n) references plus map and list overhead. The collector keeps group lists in memory; for a very large input, aggregate counts with a downstream collector or process bounded batches.",
    ["Do not assume groupingBy creates a null-key bucket.", "Do not use a sentinel that can also be a valid region.", "Do not expect map iteration order or immutable group snapshots by default."],
    ["java/collectors-tomap-duplicate-key", "java/collectors-tomap-order", "java/optional", "java/streams"],
)

add(
    "collectors-tomap-order",
    "Java Collectors.toMap: preserve encounter order with LinkedHashMap",
    "The basic toMap collector makes no map-order promise; pass a LinkedHashMap supplier when input order belongs in the output.",
    [
        ("Choose order at the collector boundary", [
            "A receipt summary displayed in arrival order should not depend on whichever map implementation a collector happens to return. The four-argument toMap overload accepts a map supplier, so the result can preserve first insertion order while duplicate keys use a declared merge rule.",
            "Updating an existing key in a default insertion-order LinkedHashMap does not move it to the end. The program retains the first position of RC-47 even though its amount is replaced. [[java/linkedhashmap|LinkedHashMap behavior]] explains when an access-order map would differ.",
        ]),
        ("Keep parallel assumptions separate", [
            "Encounter order and merge behavior should be specified before using a parallel stream. A side-effecting merge function is unsafe; an associative value merge is easier to reason about. [[java/stream-parallel-encounter-order|Parallel encounter order]] covers terminal behavior.",
        ]),
    ],
    '''import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.stream.Collectors;

public class ReceiptArrivalIndex {
    static final class Receipt {
        final String id;
        final int cents;
        Receipt(String id, int cents) {
            this.id = id;
            this.cents = cents;
        }
    }
    public static void main(String[] args) {
        Map<String, Integer> centsByReceipt = Arrays.asList(
                new Receipt("RC-47", 1200), new Receipt("RC-82", 3400),
                new Receipt("RC-47", 1500)).stream().collect(Collectors.toMap(
                receipt -> receipt.id,
                receipt -> receipt.cents,
                (earlier, later) -> later,
                LinkedHashMap::new));
        centsByReceipt.forEach((id, cents) ->
                System.out.println(id + "=" + cents));
    }
}''',
    "RC-47=1500\nRC-82=3400",
    "Expected collection is O(n) time and O(k) map space for k unique receipts, with extra link fields per entry compared with a plain hash map. Explicit ordering costs memory; use it only when a caller relies on stable presentation order.",
    ["Do not assume HashMap or basic toMap preserves arrival order.", "Do not expect updating a key to move it in an insertion-order LinkedHashMap.", "Do not make the merge callback depend on external mutable state."],
    ["java/linkedhashmap", "java/collectors-tomap-duplicate-key", "java/stream-parallel-encounter-order", "java/hashmap"],
)

add(
    "stream-parallel-encounter-order",
    "Java parallel streams: forEach and forEachOrdered have different order contracts",
    "A parallel stream may invoke forEach actions in any thread and order; forEachOrdered preserves encounter order when one exists.",
    [
        ("Keep computation separate from ordered output", [
            "A shipment list has encounter order. Parallel forEach does not promise its actions run in that order, so writing numbered report lines from it can scramble the report. forEachOrdered preserves encounter order for this ordered source, though the ordering constraint can reduce parallel benefit.",
            "The program deliberately prints only the ordered path. An unordered call cannot have one portable expected output. [[java/stream-peek-side-effects|peek actions]] and parallel terminal callbacks should not be treated as an audit log.",
        ]),
        ("Parallel does not make side effects safe", [
            "A non-thread-safe accumulator can lose updates regardless of which terminal method prints in order. Use a collector or reduction for values. Choose parallelism only after measuring enough CPU work to offset splitting, coordination and combining costs.",
        ]),
    ],
    '''import java.util.Arrays;
import java.util.List;

public class OrderedShipmentReport {
    public static void main(String[] args) {
        List<String> shipmentIds = Arrays.asList("SH-47", "SH-82", "SH-91");
        shipmentIds.parallelStream().forEachOrdered(System.out::println);
    }
}''',
    "SH-47\nSH-82\nSH-91",
    "The traversal remains O(n) total work. Parallel execution can use additional worker threads and coordination, while preserving encounter order limits throughput. Three strings are too little work to justify parallelism; the small fixture isolates the contract.",
    ["Do not promise forEach output order on a parallel stream.", "Do not use forEachOrdered to make a shared mutable accumulator thread-safe.", "Do not assume parallel traversal is faster for small or blocking workloads."],
    ["java/streams", "java/stream-peek-side-effects", "java/stream-reduce-identity", "java/collectors-tomap-order"],
)

add(
    "stream-reduce-identity",
    "Java Stream.reduce: identity and associative accumulator contracts",
    "A reduction identity must leave any value unchanged under the accumulator, and the accumulator must be associative for parallel reduction.",
    [
        ("Use the operation's real identity", [
            "For integer addition the identity is zero. Starting at one appears to add a single fee in a sequential pass, but a parallel reduction can apply that identity in multiple partitions. Add the fee after the reduction instead. For multiplication the identity is one.",
            "The example sums invoice amounts and adds a fixed handling fee exactly once. It uses long arithmetic to reduce overflow risk, but a long can still overflow; a financial ledger should define bounds or use a decimal representation. [[java/checked-integer-arithmetic|Overflow contracts]] apply before choosing a reduction shape.",
        ]),
        ("Avoid order-sensitive arithmetic", [
            "Subtraction and floating-point addition are not generally associative in the way parallel reduce expects. Floating-point rounding can change with grouping. If a stable money total matters, use integer minor units with overflow checks or BigDecimal under a defined scale policy.",
        ]),
    ],
    '''import java.util.Arrays;

public class InvoiceAmountReduction {
    public static void main(String[] args) {
        long amountCents = Arrays.asList(4700L, 1250L, 800L)
                .parallelStream().reduce(0L, Long::sum);
        long handlingFeeCents = 275L;
        System.out.println("amountCents=" + amountCents);
        System.out.println("withFeeCents=" + Math.addExact(amountCents, handlingFeeCents));
    }
}''',
    "amountCents=6750\nwithFeeCents=7025",
    "Summation is O(n) work and O(p) partial results for p parallel tasks, apart from the input list. Parallel scheduling overhead can exceed the useful work for small inputs. Math.addExact checks the final fee addition; check each intermediate addition too when overflow is possible.",
    ["Do not use one as the identity for addition.", "Do not use subtraction as a parallel reduction accumulator.", "Do not assume long or floating-point totals are safe for every financial input."],
    ["java/checked-integer-arithmetic", "java/stream-parallel-encounter-order", "java/streams", "java/collectors-tomap-duplicate-key"],
)

add(
    "stream-short-circuit",
    "Java Stream.anyMatch: stop on a decision, not on every element",
    "anyMatch returns true when a matching element is found; callers must not assume the predicate visits every element.",
    [
        ("Express the question as a predicate", [
            "A fraud gate needs to know whether any transaction exceeds a review threshold. A sequential anyMatch can stop once it has enough information. That makes it suitable for a decision, not for sending one notification per transaction. Parallel traversal may evaluate more elements even after the result is known.",
            "An empty stream returns false for anyMatch and true for allMatch. Choose the operation that expresses the business rule for an empty batch, rather than relying on the name alone. [[java/stream-single-use|A terminal operation consumes its stream]].",
        ]),
        ("Keep predicates pure", [
            "The predicate should inspect a transaction without mutating shared state. If every record needs validation, use an explicit pass or collect validation results; short-circuiting intentionally skips work once the answer is decided.",
        ]),
    ],
    '''import java.util.Arrays;
import java.util.List;

public class TransactionReviewGate {
    public static void main(String[] args) {
        List<Integer> transferCents = Arrays.asList(4200, 9800, 750);
        boolean needsReview = transferCents.stream()
                .anyMatch(cents -> cents > 9000);
        boolean emptyBatchNeedsReview = java.util.Collections.<Integer>emptyList()
                .stream().anyMatch(cents -> cents > 9000);
        System.out.println("needsReview=" + needsReview);
        System.out.println("emptyNeedsReview=" + emptyBatchNeedsReview);
    }
}''',
    "needsReview=true\nemptyNeedsReview=false",
    "Worst-case time is O(n) and extra pipeline space is small; the operation may stop earlier when a match is found. A parallel pipeline can spend work beyond the first match, and a predicate with I/O side effects makes both timing and coverage unpredictable.",
    ["Do not rely on a predicate running once for every element.", "Do not treat empty-input anyMatch as true.", "Do not use a short-circuit terminal operation as an audit or validation pass."],
    ["java/stream-single-use", "java/stream-peek-side-effects", "java/streams", "java/stream-parallel-encounter-order"],
)

for path in added:
    entry = lookup[path]
    entry["data"]["related"] = [{"path": target, "title": lookup[target]["title"]} for target in entry.pop("_related_paths")]

hub = lookup["java/java"]
hub["data"]["modules"].append({
    "title": "Stream and collector contracts",
    "summary": "Choose traversal, merge, grouping and order rules before turning a pipeline into a result.",
    "lessons": added,
})
hub["updated_at"] = stamp

reverse = {
    "java/streams": ["java/stream-single-use", "java/stream-short-circuit", "java/stream-reduce-identity"],
    "java/streams-reference": ["java/stream-peek-side-effects", "java/collectors-tomap-duplicate-key"],
    "java/stream-resource-lifetime": ["java/stream-single-use"],
    "java/hashmap": ["java/collectors-tomap-duplicate-key", "java/collectors-tomap-order"],
    "java/linkedhashmap": ["java/collectors-tomap-order"],
    "java/optional": ["java/collectors-groupingby-null-key"],
}
for path, targets in reverse.items():
    entry = lookup[path]
    marker = "<h2>Stream and collector contracts</h2>"
    entry["body"] = entry["body"].split(marker)[0] + marker + paragraph(
        "Continue with " + ", ".join("[[" + target + "|" + lookup[target]["title"] + "]]" for target in targets) + "."
    )
    entry["updated_at"] = stamp

FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print("Added", len(added), "Java lessons; linked from", len(reverse), "existing lessons")
