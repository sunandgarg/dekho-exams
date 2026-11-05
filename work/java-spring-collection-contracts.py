"""Add checked Java collection contracts and separately tested Spring web contracts."""
from __future__ import annotations

import datetime
import html
import json
import pathlib
import re
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILE = ROOT / "src/data/fixtures.json"
entries = json.loads(FILE.read_text())
by_path = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
added = []


def paragraph(text: str) -> str:
    return "<p>" + re.sub(
        r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda found: '<a href="/' + found[1] + '">' + found[2] + "</a>",
        html.escape(text),
    ) + "</p>"


def code(source: str, language: str = "java") -> str:
    return '<pre><code class="language-' + language + '">' + html.escape(source.strip(), quote=False) + "</code></pre>"


def add(slug, title, definition, sections, source, output, cost, mistakes, related, *, spring=False, test=""):
    path = ("spring/" if spring else "java/") + slug
    assert path not in by_path, path
    assert all(target in by_path for target in related), (path, related)
    subject = "spring-web" if spring else "java-collections"
    hub = next(row for row in entries if row["type"] == "subject" and row["subject"] == subject)
    body = paragraph(definition)
    for heading, paragraphs in sections:
        body += "<h2>" + html.escape(heading) + "</h2>" + "".join(paragraph(item) for item in paragraphs)
    body += "<h2>" + ("Checked source" if spring else "Working program") + "</h2>" + code(source)
    if spring:
        body += "<h2>Verification boundary</h2>" + paragraph(test + " runs in the downloadable Spring source kit. This excerpt omits imports and test setup; the kit includes complete source.")
    else:
        body += "<h3>Output</h3>" + code(output, "text")
    body += "<h2>Costs and boundaries</h2>" + paragraph(cost)
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in mistakes) + "</ul>"
    body += "<h2>Read next</h2>" + paragraph(", ".join("[[" + target + "|" + by_path[target]["title"] + "]]" for target in related) + ".")
    template = by_path["java/casts"].copy()
    template.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
        type="article", path=path, title=title, summary=definition, body=body,
        category="Backend Frameworks" if spring else "Programming", subject=subject,
        difficulty="Intermediate", tags=(["spring", "spring-boot", slug] if spring else ["java", "collections", slug]),
        status="published", featured=False, sort_order=780 + len(added),
        published_at=stamp, created_at=stamp, updated_at=stamp)
    template["data"] = {"subject_root": "spring/spring-boot" if spring else "java/java",
        "section_path": hub["path"], "kind": "tutorial", "content_format": "html",
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial", "seo_ready": True,
        "related": [{"path": target, "title": by_path[target]["title"]} for target in related]}
    if spring:
        template["data"].update(framework_version="Spring Boot 4.0.8 / Spring Framework 7",
            java_version="21 source-kit baseline", verification_suite=test,
            download_path="/downloads/aitrove-spring-source-kit.zip")
    else:
        template["data"].update(java_release=8, java_version="8+")
    entries.append(template)
    by_path[path] = template
    added.append(path)


add("linkedlist-listiterator-edits", "Java LinkedList ListIterator: the add, set and remove state machine",
    "A LinkedList list iterator can edit around its cursor, but set and remove require a preceding next or previous call.", [
    ("The cursor sits between nodes", ["Start between the first and second receipt. add inserts a new receipt before the next node. It leaves the cursor after the inserted node; it does not make that insertion the most recently returned element. Calling set immediately after add therefore fails with IllegalStateException.", "After next returns the original second node, set can replace it. remove can then delete that returned node. The result keeps the inserted receipt. This is safer than editing the list directly while the cursor is active. [[java/linkedlist-failfast-boundary|Fail-fast behavior]] is only a bug signal for competing edits."]),
    ("Choose cursor work for sequential edits", ["A listIterator(index) starts at a position, and locating a middle position may traverse links. Once positioned, walking and editing adjacent nodes avoids repeated indexed scans. See [[java/linkedlist-indexed-scan|indexed traversal cost]] before writing a loop that calls get(i) on every pass."])
], '''import java.util.Arrays;
import java.util.LinkedList;
import java.util.ListIterator;
public class ReceiptCursorEdit {
    public static void main(String[] args) {
        LinkedList<String> receipts = new LinkedList<>(Arrays.asList("R-10", "R-30"));
        ListIterator<String> cursor = receipts.listIterator(1);
        cursor.add("R-20");
        try { cursor.set("invalid"); }
        catch (IllegalStateException rejected) { System.out.println("set requires a returned node"); }
        System.out.println("next=" + cursor.next());
        cursor.set("R-30-reviewed");
        cursor.remove();
        System.out.println(receipts);
    }
}''', 'set requires a returned node\nnext=R-30\n[R-10, R-20]',
"Initial positioning may take O(n); a full cursor walk takes O(n) time and O(1) cursor state. The fixture checks Java 8 behavior and one invalid transition. It does not make concurrent edits safe.",
["Do not call set or remove immediately after add.", "Do not edit the backing list through another path while the cursor is active.", "Do not turn sequential edits into repeated get(index) calls."],
["java/linkedlist-cursor", "java/linkedlist-indexed-scan", "java/linkedlist-failfast-boundary"])

add("linkedlist-checked-view", "Java checkedList on LinkedList: runtime checks at a raw boundary",
    "Collections.checkedList returns a backed view that rejects inserts of the wrong runtime element type through that view.", [
    ("Guard the boundary that receives raw values", ["A legacy plugin exposes a raw List. Its attempt to insert an Integer through the checked view throws ClassCastException immediately, where the bad value enters. The original LinkedList still accepts valid strings and the view reflects them because it is backed by the same list.", "The guard is not a copy and cannot protect the underlying list if some caller still holds a direct reference. It checks runtime classes on attempted writes through the wrapper; generic type parameters alone are erased. [[java/generics|Generics]] explains compile-time checking, while [[java/collection-views|backed views]] explains ownership."]),
    ("Do not treat this as data validation", ["A String can still contain an invalid receipt identifier. Validate domain rules separately. A checked list also does not deeply inspect mutable elements or make access thread-safe."])
], '''import java.util.Collections;
import java.util.LinkedList;
import java.util.List;
public class CheckedReceiptBoundary {
    @SuppressWarnings({"rawtypes", "unchecked"})
    public static void main(String[] args) {
        LinkedList<String> receipts = new LinkedList<>();
        List<String> checked = Collections.checkedList(receipts, String.class);
        List legacyPlugin = checked;
        try { legacyPlugin.add(41); }
        catch (ClassCastException rejected) { System.out.println("wrong runtime type"); }
        checked.add("R-41");
        System.out.println(receipts);
    }
}''', 'wrong runtime type\n[R-41]',
"The wrapper delegates to the backing list and adds a runtime type check on its write paths. It does not deep-copy n elements, isolate callers holding the backing list, or validate receipt syntax.",
["Do not expose the unwrapped list to code expected to respect the guard.", "Do not confuse a String type check with receipt-format validation.", "Do not assume a checked view is immutable or synchronized."],
["java/generics", "java/collection-views", "java/linkedlist"])

add("linkedlist-retainall-equality", "Java LinkedList retainAll: duplicates survive membership filtering",
    "LinkedList.retainAll removes each element absent from the supplied collection; it does not turn the list into a set.", [
    ("Keep list multiplicity separate from membership", ["The allowed collection contains one receipt code and null. The source list holds that code twice. Both copies survive, the rejected code disappears, and null remains because the membership policy included it. If null is invalid in the domain, reject it before filtering rather than assuming retainAll cleans it.", "Matching uses equality as implemented by the elements and the argument collection. Mutable keys, inconsistent equality or unexpectedly expensive membership checks can change both behavior and cost. For a stable policy, build a dedicated immutable set of allowed identifiers and decide whether order and duplicates matter."])
], '''import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.Set;
public class ReceiptRetentionPolicy {
    public static void main(String[] args) {
        LinkedList<String> receipts = new LinkedList<>(Arrays.asList("R-11", "R-12", "R-11", null));
        Set<String> allowed = new HashSet<>(Arrays.asList("R-11", null));
        System.out.println("changed=" + receipts.retainAll(allowed));
        System.out.println(receipts);
    }
}''', 'changed=true\n[R-11, R-11, null]',
"A pass must inspect the n source elements; membership cost depends on the supplied collection's contains behavior. A hash-based allowed set normally reduces repeated lookup work, subject to correct hashCode and equals. The operation mutates the list; it is not an audit trail.",
["Do not assume retainAll deduplicates.", "Do not let an allowed null silently bypass a domain rule.", "Do not pass a slow membership collection into a large repeated filter without measuring."],
["java/linkedlist", "java/hashset", "java/equals-hashcode", "java/linkedlist-occurrences"])

add("linkedlist-subsequence-search", "Java indexOfSubList on LinkedList: find the first and last sequence",
    "Collections.indexOfSubList and lastIndexOfSubList find contiguous element sequences, not unordered membership.", [
    ("A match requires adjacency and order", ["Two occurrences of the same two-receipt sequence start at positions zero and two. The target is itself a list, and equals determines whether corresponding entries match. This is a small event-pattern search, not a general regex or a search over receipt substrings.", "For an empty target, the first index is zero and the last index is source.size(). Treat that boundary explicitly if an empty search request should be rejected by the product. [[java/kmp-search|KMP]] is a separate algorithmic lesson for long repeated patterns."]),
    ("Do not promise random-access speed", ["The JDK accepts any List implementation, including LinkedList. These methods report positions; later repeated get(index) calls on a LinkedList still traverse links. A production sequence-search workload needs representative input sizes and an appropriate representation."])
], '''import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedList;
import java.util.List;
public class ReceiptSequenceSearch {
    public static void main(String[] args) {
        LinkedList<String> events = new LinkedList<>(Arrays.asList("review", "approve", "review", "approve", "archive"));
        List<String> target = Arrays.asList("review", "approve");
        System.out.println("first=" + Collections.indexOfSubList(events, target));
        System.out.println("last=" + Collections.lastIndexOfSubList(events, target));
        System.out.println("empty-last=" + Collections.lastIndexOfSubList(events, Collections.emptyList()));
    }
}''', 'first=0\nlast=2\nempty-last=5',
"A candidate match compares sequence entries and may revisit elements for repeated prefixes. The example proves positions, not a general complexity ranking against KMP or other algorithms. The returned index is not a constant-time LinkedList node handle.",
["Do not confuse contiguous sequence search with containsAll.", "Do not ignore the empty-target policy.", "Do not repeatedly index a LinkedList after obtaining a position."],
["java/linkedlist", "java/linkedlist-indexed-scan", "java/kmp-search"])

add("map-merge-removal", "Java Map.merge: combine a value or remove its mapping",
    "Map.merge inserts a non-null value for an absent key, or remaps a present non-null value with a function whose null result removes the entry.", [
    ("An explicit removal is not zero", ["The stock ledger first combines a current quantity of three with two new units. A later correction returns null from the merge function, which removes the key. containsKey distinguishes the absent mapping from a stored zero; get alone would return null in both an absent map and a nullable-value map.", "This is a single-thread HashMap fixture. It does not turn a read-modify-write sequence into an atomic operation across threads, processes or a database. [[java/concurrent-map|ConcurrentMap]] has implementation-specific atomicity contracts, and [[spring/transactions|transactions]] are a separate persistence boundary."]),
    ("Never use null as an accidental arithmetic result", ["The supplied merge value must be non-null. Validate stock quantities and overflow before mutating a real ledger. A remapping function with external side effects can run in contexts whose retry behavior differs; keep the function small and pure when possible."])
], '''import java.util.HashMap;
import java.util.Map;
public class StockLedgerMerge {
    public static void main(String[] args) {
        Map<String, Integer> quantities = new HashMap<>();
        quantities.put("SKU-7", 3);
        quantities.merge("SKU-7", 2, Integer::sum);
        System.out.println("after delivery=" + quantities.get("SKU-7"));
        quantities.merge("SKU-7", 1, (current, correction) -> null);
        System.out.println("present=" + quantities.containsKey("SKU-7"));
    }
}''', 'after delivery=5\npresent=false',
"For this HashMap fixture, lookup and update have expected constant-time behavior with a suitable hash distribution; that is not a worst-case or cross-process guarantee. The remapping call is not a database transaction.",
["Do not treat removal as a numeric zero.", "Do not assume a HashMap merge protects concurrent writers.", "Do not hide overflow or invalid corrections inside a remapping function."],
["java/hashmap", "java/concurrent-map", "java/equals-hashcode", "spring/transactions"])

add("map-compute-if-absent-null", "Java computeIfAbsent: null means no new mapping",
    "Map.computeIfAbsent calls its mapping function when the key is absent or mapped to null, and stores only a non-null result.", [
    ("The null case has two meanings", ["A missing receipt key returns null from the loader, so the map remains without that key. Another key already mapped to null is treated as needing a value; the loader fills it. containsKey reveals the initial null mapping, while get cannot distinguish it from absence.", "If a loader can fail, prefer an explicit result or exception over returning null ambiguously. The mapping function should not structurally edit the same map. [[java/map-merge-removal|merge]] solves a different case: combining a supplied value with an existing one."]),
    ("Do not infer once-only concurrent loading", ["This program uses a plain HashMap and no concurrent calls. Loading from a remote service needs a separate cache-stampede, timeout and stale-value policy. A ConcurrentHashMap's computeIfAbsent contract differs from the default Map operation and should be tested under its own boundary."])
], '''import java.util.HashMap;
import java.util.Map;
public class ReceiptLookupCache {
    public static void main(String[] args) {
        Map<String, String> receiptState = new HashMap<>();
        receiptState.put("R-41", null);
        System.out.println("present-null=" + receiptState.containsKey("R-41"));
        System.out.println("missing=" + receiptState.computeIfAbsent("R-99", id -> null));
        System.out.println("stored-missing=" + receiptState.containsKey("R-99"));
        System.out.println("loaded=" + receiptState.computeIfAbsent("R-41", id -> "reviewed"));
    }
}''', 'present-null=true\nmissing=null\nstored-missing=false\nloaded=reviewed',
"Expected HashMap lookup cost depends on hash distribution. A mapping function may do arbitrary work, so do not report the whole operation as constant time without including that work. This fixture does not test concurrent loading.",
["Do not use get == null when presence matters.", "Do not assume a null loader result is cached.", "Do not infer a cross-thread single-loader guarantee from a plain Map example."],
["java/hashmap", "java/map-merge-removal", "java/concurrent-map", "spring/cache-keys"])

add("priorityqueue-tie-order", "Java PriorityQueue: define tie order in the comparator",
    "PriorityQueue removes a least-ranked element according to its comparator, but equal-ranked elements have no specified removal order.", [
    ("Specify the secondary key", ["Two jobs have the same urgency. A comparator that only compares urgency would leave their relative removal order unspecified. This queue compares urgency first, then receipt ID, producing a repeatable order for the example.", "The queue's iterator does not expose priority order. Poll repeatedly if you need the ordered sequence, or copy the queue if the original must remain intact. [[java/priorityqueue|PriorityQueue basics]] covers heap operations; [[java/comparator-contracts|comparator contracts]] covers transitivity and equality decisions."]),
    ("Tie rules are business rules", ["Lexical ID order is only a deliberate fixture policy. A real scheduler may need submission sequence, deadline, fairness or tenant quotas. Encode those rules explicitly and test the rejected or equal-key cases."])
], '''import java.util.Comparator;
import java.util.PriorityQueue;
public class ReceiptReviewOrder {
    static final class ReviewJob {
        final String receiptId; final int urgency;
        ReviewJob(String receiptId, int urgency) { this.receiptId = receiptId; this.urgency = urgency; }
    }
    public static void main(String[] args) {
        PriorityQueue<ReviewJob> jobs = new PriorityQueue<>(
            Comparator.comparingInt((ReviewJob job) -> job.urgency)
                .thenComparing(job -> job.receiptId));
        jobs.add(new ReviewJob("R-42", 1));
        jobs.add(new ReviewJob("R-41", 1));
        jobs.add(new ReviewJob("R-43", 2));
        while (!jobs.isEmpty()) System.out.println(jobs.poll().receiptId);
    }
}''', 'R-41\nR-42\nR-43',
"Insertion and removal are O(log n) for n queued jobs; inspecting the head is O(1). Draining n jobs costs O(n log n). The queue does not provide stable ordering for comparator ties or sorted iterator order.",
["Do not assume insertion order breaks priority ties.", "Do not print the iterator and call it sorted output.", "Do not subtract integer priorities in a comparator where overflow is possible."],
["java/priorityqueue", "java/comparator-contracts", "java/binary-heap"])

add("linkedlist-removeif-policy", "Java LinkedList removeIf: keep a predicate narrow and side-effect free",
    "LinkedList.removeIf removes every element for which a predicate returns true while preserving the order of survivors.", [
    ("Define the removal rule before mutating", ["A retry queue holds expired and live receipts. The predicate removes only IDs with the expired prefix. The remaining entries retain their relative order, and the returned boolean reports whether anything changed.", "The predicate sees each element during traversal. Do not mutate the same list from inside it or depend on a partially processed list after the predicate throws. If rejection must leave the original untouched, validate first or build a new list and publish it only after success. [[java/linkedlist-cursor|Cursor edits]] are a separate explicit mutation path."]),
    ("Keep the domain rule separate", ["Prefix matching is only a fixture. A real expiry rule needs a clock and a parsed deadline; [[java/clock-injection|injecting time]] avoids inconsistent tests. A List is also a poor choice when the primary operation is repeatedly finding one receipt by ID."])
], '''import java.util.Arrays;
import java.util.LinkedList;
public class ExpiredReceiptCleanup {
    public static void main(String[] args) {
        LinkedList<String> pending = new LinkedList<>(Arrays.asList(
            "live:R-41", "expired:R-39", "live:R-42", "expired:R-40"));
        boolean changed = pending.removeIf(id -> id.startsWith("expired:"));
        System.out.println("changed=" + changed);
        System.out.println(pending);
    }
}''', 'changed=true\n[live:R-41, live:R-42]',
"A full removal pass inspects n elements and needs no separate survivor list in this fixture. Predicate work adds to that cost. Do not claim transaction semantics or a rollback guarantee for predicate failure.",
["Do not mutate the backing list from inside its predicate.", "Do not treat a throwing predicate as an all-or-nothing operation.", "Do not encode production expiry as a string prefix."],
["java/linkedlist", "java/linkedlist-cursor", "java/clock-injection"])

add("receipt-media-types", "Spring MVC consumes and produces: 415 and 406 are different failures",
    "A Spring MVC mapping can constrain the request Content-Type with consumes and the requested response type with produces.", [
    ("Two headers, two decisions", ["The checked controller accepts JSON input and produces JSON output. A matching request returns 200. Sending text/plain as the request body returns 415 Unsupported Media Type. Sending valid JSON while asking only for text/plain returns 406 Not Acceptable. Those statuses answer different client mistakes.", "A request body can still be invalid JSON or invalid domain data after its media type matches. [[spring/rest-validation|Request validation]] handles that boundary; [[spring/nested-receipt-validation|nested field validation]] checks inside a deserialized object."]),
    ("This is a mapping test", ["MockMvc exercises Spring's mapping and conversion path without a proxy or real network. It does not establish API version negotiation, a maximum request size, charset policy, or safe error bodies for every converter failure. Add explicit integration tests before publishing a compatibility guarantee."])
], '''@PostMapping(path = "/contract/imports", consumes = "application/json", produces = "application/json")
String importReceipt(@RequestBody String request) {
    return "{\"accepted\":true}";
}

// MockMvc checks 200 for JSON/JSON, 415 for text/plain input,
// and 406 for an Accept header that permits only text/plain.''', "",
"This test covers one controller and three header combinations. It does not exercise a deployed reverse proxy, streaming upload, body-size limit or versioned representation.",
["Do not conflate the request Content-Type with the response Accept header.", "Do not assume accepted media type means valid JSON or valid receipt data.", "Do not claim an API versioning policy from a single produces value."],
["spring/rest-validation", "spring/problem-details", "java/http-client"], spring=True,
test="ReceiptMediaTypeTest.separatesRequestTypeFromAcceptableResponseType")

add("nested-receipt-validation", "Spring MVC nested validation: reject a bad line before the handler",
    "@Valid on a request body triggers Bean Validation, and @Valid on a nested field requests validation of that nested object.", [
    ("The cascade is explicit", ["The request wrapper has a nonblank receipt ID. Its nested line has a nonblank SKU and a positive quantity. The test accepts a valid object, rejects quantity zero, and rejects a blank receipt ID with 400. The handler runs only for the valid request.", "A missing line is a different case: @Valid alone does not require the nested object to exist. Add @NotNull when a line is mandatory. A nonblank ID is not proof that the receipt exists or belongs to the caller; that requires separate service and authorization checks."]),
    ("Keep error output controlled", ["The fixture verifies status, not a production problem body. Error responses should avoid echoing sensitive raw values and should use field identifiers that clients can handle. [[spring/problem-details|Problem details]] covers that response shape."])
], '''static class ReceiptLine {
    @NotBlank public String sku;
    @Positive public int quantity;
}
static class ReceiptImport {
    @NotBlank public String receiptId;
    @Valid public ReceiptLine line;
}
@PostMapping(path = "/contract/validated-imports", consumes = "application/json")
String accept(@Valid @RequestBody ReceiptImport request) {
    return request.receiptId;
}''', "",
"MockMvc checks one valid request and two invalid fields using an in-process validator. It does not prove authorization, persistence, every malformed JSON shape, or a production error contract.",
["Do not omit @Valid on the nested field when cascade validation is intended.", "Do not assume @Valid means a missing nested object is rejected; add @NotNull if required.", "Do not treat format validation as a tenant-ownership check."],
["spring/rest-validation", "spring/problem-details", "spring/tenant-receipt-authorization"], spring=True,
test="NestedReceiptValidationTest.rejectsInvalidNestedFieldsBeforeCallingTheHandler")

for subject, module_title in (("java-collections", "Collection mutation and lookup contracts"),
                              ("spring-web", "Request type and nested validation")):
    hub = next(row for row in entries if row["type"] == "subject" and row["subject"] == subject)
    paths = [path for path in added if by_path[path]["subject"] == subject]
    hub["data"]["modules"].append({"title": module_title,
        "summary": "Run the checked example, then inspect its rejected path and cost boundary.", "lessons": paths})
    hub["updated_at"] = stamp
    if subject == "spring-web":
        links = "<ul>" + "".join('<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>"
            for module in hub["data"]["modules"] for path in module["lessons"]) + "</ul>"
        hub["body"] = re.sub(r"(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)",
            lambda match: match[1] + links + match[2], hub["body"])

reverse = {
    "java/linkedlist": ["java/linkedlist-listiterator-edits", "java/linkedlist-checked-view", "java/linkedlist-retainall-equality", "java/linkedlist-subsequence-search", "java/linkedlist-removeif-policy"],
    "java/hashmap": ["java/map-merge-removal", "java/map-compute-if-absent-null"],
    "java/priorityqueue": ["java/priorityqueue-tie-order"],
    "spring/rest-validation": ["spring/receipt-media-types", "spring/nested-receipt-validation"],
}
for path, targets in reverse.items():
    row = by_path[path]
    marker = "<h2>Continue with collection and web contracts</h2>"
    row["body"] = row["body"].split(marker)[0] + marker + paragraph("Continue with " + ", ".join(
        "[[" + target + "|" + by_path[target]["title"] + "]]" for target in targets) + ".")
    row["updated_at"] = stamp

FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"added": added, "count": len(added)}))
