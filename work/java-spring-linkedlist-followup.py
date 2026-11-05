"""Add checked LinkedList boundary lessons and separate Spring contracts."""
from __future__ import annotations

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
added: list[str] = []


def p(value: str) -> str:
    escaped = html.escape(value)
    return "<p>" + re.sub(r"\[\[([^|]+)\|([^\]]+)\]\]", lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>", escaped) + "</p>"


def code(value: str, language: str = "java") -> str:
    return '<pre><code class="language-' + language + '">' + html.escape(value.strip(), quote=False) + "</code></pre>"


def put(slug, title, definition, sections, source, output, cost, mistakes, related, *, subject="java-collections", spring=False, proof=""):
    path = ("spring/" if spring else "java/") + slug
    assert path not in lookup, path
    assert all(target in lookup for target in related), (path, related)
    hub = next(entry for entry in entries if entry["type"] == "subject" and entry["subject"] == subject)
    body = p(definition)
    body += p("The downloadable Spring source kit checks this boundary with the named JUnit test and its pinned dependencies." if spring else "The Java 8 program below compiles without external libraries; its output is checked against a real run.")
    for heading, parts in sections:
        body += "<h2>" + html.escape(heading) + "</h2>" + "".join(p(part) for part in parts)
    body += "<h2>" + ("Checked source" if spring else "Working program") + "</h2>" + code(source)
    if spring:
        body += "<h2>Verification boundary</h2>" + p(proof + " runs in the Spring source kit. This excerpt omits imports and surrounding test setup; the downloadable kit contains the complete source.")
    else:
        body += "<h3>Output</h3>" + code(output, "text")
    body += "<h2>Costs and boundaries</h2>" + p(cost)
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in mistakes) + "</ul>"
    body += "<h2>Read next</h2>" + p(", ".join("[[" + target + "|" + lookup[target]["title"] + "]]" for target in related) + ".")
    entry = copy.deepcopy(lookup["java/casts"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), path=path, title=title, summary=definition, body=body, category="Backend Frameworks" if spring else "Programming", subject=subject, difficulty="Intermediate", tags=["spring", "spring-boot", slug] if spring else ["java", "linkedlist", slug], status="published", featured=False, sort_order=740 + len(added), published_at=stamp, created_at=stamp, updated_at=stamp)
    entry["data"] = {"subject_root": "spring/spring-boot" if spring else "java/java", "section_path": hub["path"], "kind": "tutorial", "content_format": "html", "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)), "author_path": "authors/aitrove-editorial", "related": [{"path": target, "title": lookup[target]["title"]} for target in related], "seo_ready": True}
    if spring:
        entry["data"].update(framework_version="Spring Boot 4.0.8 / Spring Framework 7", java_version="21 source-kit baseline", verification_suite=proof, download_path="/downloads/aitrove-spring-source-kit.zip")
    else:
        entry["data"].update(java_release=8, java_version="8+")
    entries.append(entry)
    lookup[path] = entry
    added.append(path)


put("linkedlist-sublist-view", "Java LinkedList subList: a live window, not a snapshot", "LinkedList.subList returns a backed view whose permitted edits change the original list.", [
    ("Treat the window as shared state", ["A billing batch keeps four receipt identifiers and exposes only its middle two to a correction step. Setting one value through the window updates the original list. Clearing the window removes those two nodes from the backing list; the end elements remain.", "The method returns a view, not a detached copy. If a caller needs a stable membership snapshot, construct a new list from the window and decide separately whether its element objects must be copied. [[java/collection-views|View ownership]] covers that second question."]),
    ("Keep structural changes inside the view", ["The List contract says the view's semantics become undefined if the backing list is structurally changed outside the view. A particular JVM may throw a ConcurrentModificationException after that mistake, but code should not depend on the exception. Instead, keep one owner for structural edits or rebuild the window after the parent changes."])
], '''import java.util.Arrays;
import java.util.LinkedList;
import java.util.List;
public class ReceiptCorrectionWindow {
    public static void main(String[] args) {
        LinkedList<String> receipts = new LinkedList<>(Arrays.asList("R-11", "R-12", "R-13", "R-14"));
        List<String> window = receipts.subList(1, 3);
        window.set(0, "R-12-rechecked");
        System.out.println(receipts);
        window.clear();
        System.out.println(receipts);
    }
}''', '[R-11, R-12-rechecked, R-13, R-14]\n[R-11, R-14]', "Obtaining a subList is a view operation; locating and changing a linked-list position may traverse nodes. Clearing k elements still changes the backing structure. The view retains a reference to that structure rather than allocating k independent elements.", ["Do not call a backed view an immutable snapshot.", "Do not structurally mutate the parent while continuing to use an old view.", "Do not assume copying list membership deep-copies mutable elements."], ["java/linkedlist", "java/collection-views", "java/linkedlist-shallow-copy"])

put("linkedlist-reverse-traversal", "Java LinkedList descendingIterator: inspect and remove from the tail", "LinkedList.descendingIterator visits nodes from tail to head without first copying them into another collection.", [
    ("Use the iterator for the edit", ["A retry queue holds three receipt states. The cursor reads the newest state first and removes the retry state through its own remove method. That is a cursor-local structural edit. Calling queue.remove while the cursor is active would create a different mutation path.", "The fixture records the order it saw and then prints the remaining queue in its original head-to-tail order. Reverse traversal does not reverse the underlying list. For a permanent reordered list, use an explicit mutation or copy policy."]),
    ("Do not use fail-fast as a lock", ["This iterator is still part of a mutable LinkedList. If another thread changes the queue, synchronize access or give a single worker ownership; an exception is a best-effort bug signal, not an isolation guarantee. See [[java/synchronized-list-iteration|whole-traversal locking]] for the wrapper contract."])
], '''import java.util.Arrays;
import java.util.Iterator;
import java.util.LinkedList;
public class RetryQueueReverseRead {
    public static void main(String[] args) {
        LinkedList<String> states = new LinkedList<>(Arrays.asList("queued", "retry", "settled"));
        StringBuilder seen = new StringBuilder();
        for (Iterator<String> cursor = states.descendingIterator(); cursor.hasNext();) {
            String state = cursor.next();
            if (seen.length() > 0) seen.append(',');
            seen.append(state);
            if (state.equals("retry")) cursor.remove();
        }
        System.out.println(seen);
        System.out.println(states);
    }
}''', 'settled,retry,queued\n[queued, settled]', "A full descending scan is O(n) time with O(1) cursor state, excluding the output string. Removing the current known node avoids a separate value search; it does not make arbitrary lookup constant time.", ["Do not call list.remove while expecting an existing cursor to stay valid.", "Do not mistake reverse iteration for a reversed copy.", "Do not use fail-fast behavior for thread coordination."], ["java/linkedlist", "java/linkedlist-cursor", "java/synchronized-list-iteration"])

put("linkedlist-typed-array", "Java LinkedList toArray(T[]): the null terminator boundary", "LinkedList.toArray(T[]) writes list members into a typed array and sets the first spare slot to null when the supplied array is larger.", [
    ("Only one spare slot is reset", ["The supplied array starts with old values. Two receipt identifiers replace its first two positions, index two becomes null, and index three retains its old value. The API does not promise to clear the entire unused tail. A downstream reader that scans every slot can accidentally process stale data.", "If the supplied array is too small, the method allocates another array with the supplied runtime component type. Always use the returned reference; assuming the original was filled is wrong in that case."]),
    ("Null may also be a member", ["LinkedList permits null elements. The first null in a typed array is not a reliable length marker unless the application prohibits null members. Use the known list size or the returned array length according to the receiving API's contract. [[java/linkedlist-null-head|Null head ambiguity]] is the same policy problem at a different boundary."])
], '''import java.util.Arrays;
import java.util.LinkedList;
public class ReceiptArrayExport {
    public static void main(String[] args) {
        LinkedList<String> receipts = new LinkedList<>(Arrays.asList("R-21", "R-22"));
        String[] reusable = {"old-0", "old-1", "old-2", "old-3"};
        String[] exported = receipts.toArray(reusable);
        System.out.println("same array=" + (exported == reusable));
        System.out.println(Arrays.toString(exported));
    }
}''', 'same array=true\n[R-21, R-22, null, old-3]', "Copying n references into an array is O(n) time. A sufficiently large supplied array avoids allocating a new array, but retained element objects are still shared; the operation does not deep-copy them.", ["Do not read the entire oversized array as fresh list data.", "Do not use null as a length marker while null list elements are legal.", "Do not discard the returned array when the input array may be too small."], ["java/linkedlist", "java/linkedlist-null-head", "java/linkedlist-shallow-copy"])

put("linkedlist-stable-sort", "Java LinkedList sort: stable order needs temporary array work", "List.sort orders a modifiable LinkedList by a comparator while preserving the relative order of equal-ranked elements.", [
    ("State the tie rule", ["Three receipts arrive in order R-11, R-12, R-13. Sorting by priority moves R-12 first while R-11 remains before R-13 because both have priority two. That stable tie behavior is useful only if encounter order itself is meaningful and retained through earlier processing.", "A comparator must provide a consistent ordering. Subtracting large integer priorities to compare them can overflow; Comparator.comparingInt avoids that arithmetic. [[java/comparator-contracts|Comparator contracts]] covers transitivity and equality issues."]),
    ("Do not assume pointer relinking removes memory cost", ["The Java 8 List default sort obtains an array, sorts it, then writes values back through a list iterator. LinkedList nodes remain, but the algorithm still needs array storage. For repeated indexed queries after sorting, an array-backed representation may serve the workload better."])
], '''import java.util.Arrays;
import java.util.Comparator;
import java.util.LinkedList;
public class ReceiptPrioritySort {
    static final class Receipt {
        final String id; final int priority;
        Receipt(String id, int priority) { this.id = id; this.priority = priority; }
        public String toString() { return id; }
    }
    public static void main(String[] args) {
        LinkedList<Receipt> receipts = new LinkedList<>(Arrays.asList(
            new Receipt("R-11", 2), new Receipt("R-12", 1), new Receipt("R-13", 2)));
        receipts.sort(Comparator.comparingInt(receipt -> receipt.priority));
        System.out.println(receipts);
    }
}''', '[R-12, R-11, R-13]', "General comparison sorting is O(n log n) in the worst case. The Java 8 default List.sort uses an array of n references plus sorting workspace; no claim of in-place constant memory is made.", ["Do not use subtraction as a general integer comparator.", "Do not assume stable order can repair an earlier unordered source.", "Do not assume a linked structure removes the sort's array allocation."], ["java/linkedlist", "java/comparator-contracts", "java/arraylist"])

put("linkedlist-binary-search", "Java LinkedList binarySearch: comparisons are not the whole cost", "Collections.binarySearch can search a sorted LinkedList, but locating positions in a non-random-access list still traverses links.", [
    ("Sort under the same ordering", ["The search contract requires ascending order under the same comparison used by the search. The fixture finds twenty at position one. Thirty is absent, so the negative result encodes insertion point two. Decode a negative result as -result-1, not as an array position to index directly.", "If equal values occur several times, the returned matching index is not specified to be the first duplicate. A range lookup needs a separate lower-bound policy."]),
    ("Choose a structure for repeated reads", ["For a large non-RandomAccess list, the JDK uses iterator-based search with O(n) link traversals and O(log n) comparisons. A small fixture cannot measure that cost. If the workload needs repeated random-access binary searches, an ArrayList or primitive array may better fit; if it needs key lookup, consider a map."])
], '''import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedList;
public class SortedReceiptCodeLookup {
    public static void main(String[] args) {
        LinkedList<Integer> codes = new LinkedList<>(Arrays.asList(10, 20, 40));
        int found = Collections.binarySearch(codes, 20);
        int missing = Collections.binarySearch(codes, 30);
        System.out.println("found=" + found);
        System.out.println("missing=" + missing + ", insert=" + (-missing - 1));
    }
}''', 'found=1\nmissing=-3, insert=2', "For a large LinkedList, the API documents O(n) link traversals and O(log n) comparisons. The index returned is a position, not a constant-time path to that node for later get(index) calls.", ["Do not search an unsorted list and interpret the result.", "Do not promise O(log n) total work solely from the algorithm's name.", "Do not assume the first equal element is returned."], ["java/linkedlist", "java/linkedlist-indexed-scan", "java/arraylist", "java/hashmap"])

put("linkedlist-failfast-boundary", "Java LinkedList fail-fast iterators: a bug signal, not safety", "A LinkedList iterator may detect structural changes made outside that iterator and report ConcurrentModificationException.", [
    ("The single-thread fixture exposes the mistake", ["The cursor reads one receipt, then the program appends another through the list. On this checked runtime the next cursor step throws. That is a diagnostic for a violated traversal contract. The original list still contains the new receipt.", "A correct single-thread edit can use the iterator's own remove method, as in [[java/linkedlist-reverse-traversal|reverse traversal]], or finish the traversal before mutating the list. Do not catch the exception and pretend the loop completed all items."]),
    ("No concurrency guarantee follows", ["Oracle describes fail-fast behavior as best effort under unsynchronized concurrent change. It cannot be used to assert that all races are detected or that partial work rolled back. A shared queue needs a synchronization or ownership policy, not an exception handler."])
], '''import java.util.Arrays;
import java.util.ConcurrentModificationException;
import java.util.Iterator;
import java.util.LinkedList;
public class ReceiptCursorInvalidation {
    public static void main(String[] args) {
        LinkedList<String> receipts = new LinkedList<>(Arrays.asList("R-31", "R-32"));
        Iterator<String> cursor = receipts.iterator();
        System.out.println("first=" + cursor.next());
        receipts.addLast("R-33");
        try { cursor.next(); }
        catch (ConcurrentModificationException invalidated) { System.out.println("cursor invalidated"); }
        System.out.println(receipts);
    }
}''', 'first=R-31\ncursor invalidated\n[R-31, R-32, R-33]', "The example has no concurrent thread; it checks one deterministic misuse on the local runtime. Iterator traversal is O(n) for n elements. Exception detection is not an atomic snapshot or a synchronization mechanism.", ["Do not depend on fail-fast exceptions to prove absence of races.", "Do not continue a partially processed batch as though traversal succeeded.", "Do not make structural changes through the list while an iterator owns the edit path."], ["java/linkedlist", "java/linkedlist-cursor", "java/synchronized-list-iteration"])

put("session-scope-boundary", "Spring session scope: one target across requests, separate targets across sessions", "A session-scoped proxy resolves state for the active HTTP session while a singleton service holds the proxy reference.", [
    ("Prove the lifetime with two sessions", ["The test binds two mock requests to the same session, then a third request to another session. The first counter returns one and two; the second starts at one. The service is still a singleton. The proxy changes which ReviewCounter instance receives each method call.", "A session scope does not establish that the session belongs to an authenticated user. Session fixation, expiry, storage across nodes and tenant authorization need separate policies. Do not place unbounded receipt histories in a session-scoped bean."]),
    ("Keep background work explicit", ["A worker without an active web request cannot assume this proxy will resolve to a session target. Pass a narrow authorized identifier or immutable command into background work. [[spring/request-scope-proxy|Request scope]] has a shorter lifetime and the same proxy-dispatch rule."])
], '''@Bean @SessionScope(proxyMode = ScopedProxyMode.TARGET_CLASS)
ReviewCounter reviewCounter() { return new ReviewCounter(); }
@Bean ReviewService reviewService(ReviewCounter counter) { return new ReviewService(counter); }

// The test binds two requests to session A, then one to session B.
assertEquals(1, viewInSession(service, first));
assertEquals(2, viewInSession(service, first));
assertEquals(1, viewInSession(service, second));''', "", "The test checks local scope identity only. It does not exercise browser cookies, clustered session stores, concurrent requests sharing one session, session expiry, or any identity-provider integration.", ["Do not equate a session object with an authorized user.", "Do not store unbounded application history in session memory.", "Do not access the proxy from background work without an explicit context handoff."], ["spring/bean-scopes", "spring/request-scope-proxy", "spring/async-boundaries"], subject="spring-core", spring=True, proof="SessionScopeBoundaryTest.retainsStateAcrossRequestsButNotAcrossSessions")

put("conditional-receipt-get", "Spring MVC conditional GET: validate the representation tag", "A controller can return an ETag so a later matching If-None-Match GET receives 304 without a response body.", [
    ("The tag belongs to the representation", ["The fixture serves a fixed receipt version with ETag receipt-7-v3. A matching conditional GET returns 304 and an empty body. A stale tag returns 200 and the current body. A missing receipt remains 404; a cache tag cannot turn an absent resource into a valid one.", "The code uses Cache-Control: no-cache so a cache may store the representation but must revalidate it before reuse. In a real service, compute a tag from the correct version of the selected representation, including any user-specific visibility boundary. A fixed literal is only a teaching fixture."]),
    ("Bandwidth is not authorization", ["An ETag is a cache validator. It is not proof that the caller may see a receipt. A reverse proxy or shared cache must respect authentication and cache-control rules. An If-Match write precondition is a separate mutation contract, not implemented by this GET test."])
], '''@GetMapping("/contract/receipts/{id}")
ResponseEntity<String> read(@PathVariable int id) {
    if (id != 7) return ResponseEntity.notFound().build();
    return ResponseEntity.ok()
        .cacheControl(CacheControl.noCache())
        .eTag("receipt-7-v3")
        .body("receipt:7:reviewed");
}''', "", "MockMvc checks the response status, tag and body for current, matching and stale requests. This fixed in-process controller does not measure upstream computation, proxy caching, deployment behavior or private-data isolation.", ["Do not treat ETag possession as permission to read a resource.", "Do not reuse one tag across different visible representations.", "Do not claim a shallow ETag filter avoids generating the response body."], ["spring/rest-validation", "spring/pagination-bounds", "spring/security-filter-chain"], subject="spring-web", spring=True, proof="ConditionalReceiptHttpTest.returnsA304OnlyForTheMatchingRepresentationTag")

put("tenant-receipt-authorization", "Spring method authorization: reject a cross-tenant read", "A proxied service can compare the requested tenant with the authenticated principal before returning a tenant-scoped receipt.", [
    ("Check the resource scope at the service", ["The local test authenticates tenant-east, allows its receipt seven, and rejects the same method call for tenant-west. The rule uses the first method argument and Spring Security's authenticated name. It is applied to the managed bean, which means the call passes through method-security advice.", "A broad receipt.read authority alone would not answer which tenant's receipt the caller may read. [[spring/jwt-resource-server|JWT validation]] establishes one trust input; this lesson adds a resource-specific decision after authentication. The identity and tenant mapping in this test are fixtures, not a production issuer or database policy."]),
    ("Avoid bypasses and data leaks", ["Directly constructing the service skips its proxy. A public controller should not return a row before applying this check, including through list and export endpoints. A database query scoped by trusted tenant can reduce accidental cross-tenant reads, but must be tested against the target database and repository code."])
], '''static class TenantReceiptReader {
    @PreAuthorize("#p0 == authentication.name")
    public String read(String tenant, int receiptId) {
        return tenant + ":" + receiptId;
    }
}''', "", "The test uses one local principal and one managed service method. It does not prove row-level filtering, real token-to-tenant mapping, identity-store correctness or authorization across every endpoint.", ["Do not confuse a valid token or broad scope with resource ownership.", "Do not call a directly constructed object and expect proxy advice.", "Do not accept a caller-controlled tenant header as authenticated identity."], ["spring/method-authorization", "spring/jwt-resource-server", "spring/security-filter-chain", "java/interfaces"], subject="spring-security", spring=True, proof="TenantReceiptAuthorizationTest.rejectsACrossTenantReadThroughTheManagedService")

labels = {"java-collections": "LinkedList views, traversal and conversion", "spring-core": "Session-bound dependencies", "spring-web": "Conditional HTTP representations", "spring-security": "Tenant-scoped service reads"}
for subject in sorted({lookup[path]["subject"] for path in added}):
    hub = next(entry for entry in entries if entry["type"] == "subject" and entry["subject"] == subject)
    hub["data"]["modules"].append({"title": labels[subject], "summary": "Read the contract, run the checked fixture and inspect the rejected path.", "lessons": [path for path in added if lookup[path]["subject"] == subject]})
    hub["updated_at"] = stamp
    if hub["path"].startswith("spring/"):
        lesson_links = "<ul>" + "".join('<li><a href="/' + path + '">' + html.escape(lookup[path]["title"]) + "</a></li>" for module in hub["data"]["modules"] for path in module["lessons"]) + "</ul>"
        hub["body"] = re.sub(r"(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)", lambda match: match[1] + lesson_links + match[2], hub["body"])

reverse = {
    "java/linkedlist": ["java/linkedlist-sublist-view", "java/linkedlist-reverse-traversal", "java/linkedlist-typed-array", "java/linkedlist-stable-sort", "java/linkedlist-binary-search", "java/linkedlist-failfast-boundary"],
    "java/collection-views": ["java/linkedlist-sublist-view"],
    "java/linkedlist-cursor": ["java/linkedlist-reverse-traversal", "java/linkedlist-failfast-boundary"],
    "java/linkedlist-indexed-scan": ["java/linkedlist-binary-search"],
    "java/comparator-contracts": ["java/linkedlist-stable-sort"],
    "spring/bean-scopes": ["spring/session-scope-boundary"],
    "spring/request-scope-proxy": ["spring/session-scope-boundary"],
    "spring/rest-validation": ["spring/conditional-receipt-get"],
    "spring/method-authorization": ["spring/tenant-receipt-authorization"],
    "spring/jwt-resource-server": ["spring/tenant-receipt-authorization"],
}
for path, targets in reverse.items():
    entry = lookup[path]
    marker = "<h2>Continue with the new boundary checks</h2>"
    entry["body"] = entry["body"].split(marker)[0] + marker + p("Continue with " + ", ".join("[[" + target + "|" + lookup[target]["title"] + "]]" for target in targets) + ".")
    entry["updated_at"] = stamp

FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"added": added, "count": len(added)}))
