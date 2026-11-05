"""Add original Java and Spring lessons while preserving the existing curriculum."""
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
added = []


def paragraph(value: str) -> str:
    escaped = html.escape(value)
    linked = re.sub(
        r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>",
        escaped,
    )
    return "<p>" + linked + "</p>"


def block(source: str, language: str = "java") -> str:
    return '<pre><code class="language-' + language + '">' + html.escape(source.strip(), quote=False) + "</code></pre>"


def article(slug, title, definition, sections, source, output, cost, mistakes, related, *, subject="java-collections", release=8, spring=False, proof=""):
    path = ("spring/" if spring else "java/") + slug
    assert path not in lookup, path
    for target in related:
        assert target in lookup or target in added, (path, target)
    body = paragraph(definition)
    if spring:
        body += paragraph("The Spring source kit uses Java 21 and its pinned Spring Boot dependencies. Run the named JUnit test to check this boundary.")
    else:
        body += paragraph(f"This complete Java {release} program has a checked output. Compile it as the named public class, then run it without additional libraries.")
    for heading, prose in sections:
        body += "<h2>" + html.escape(heading) + "</h2>" + "".join(paragraph(part) for part in prose)
    body += "<h2>" + ("Checked contract" if spring else "Working program") + "</h2>" + block(source)
    if spring:
        body += "<h2>How it is checked</h2>" + paragraph(proof + " covers this behavior in the source kit. The displayed code is the test boundary; the kit contains its imports and configuration.")
    else:
        body += "<h3>Output</h3>" + block(output, "text")
    body += "<h2>Costs and boundaries</h2>" + paragraph(cost)
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in mistakes) + "</ul>"
    body += "<h2>Read next</h2>" + paragraph(", ".join(f"[[{target}|{lookup[target]['title']}]]" for target in related) + ".")
    hub = next(entry for entry in entries if entry["type"] == "subject" and entry["subject"] == subject)
    template = lookup["java/casts"]
    entry = copy.deepcopy(template)
    entry.update(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
        path=path,
        title=title,
        summary=definition,
        body=body,
        category="Backend Frameworks" if spring else "Programming",
        subject=subject,
        difficulty="Intermediate",
        tags=["spring", "spring-boot", slug] if spring else ["java", slug],
        status="published",
        featured=False,
        sort_order=700 + len(added),
        published_at=stamp,
        created_at=stamp,
        updated_at=stamp,
    )
    entry["data"] = {
        "subject_root": "spring/spring-boot" if spring else "java/java",
        "section_path": hub["path"],
        "kind": "tutorial",
        "content_format": "html",
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial",
        "related": [{"path": target, "title": lookup[target]["title"]} for target in related],
        "seo_ready": True,
    }
    if spring:
        entry["data"].update(framework_version="Spring Boot 4.0.8 / Spring Framework 7", java_version="21 source-kit baseline", verification_suite=proof, download_path="/downloads/aitrove-spring-source-kit.zip")
    else:
        entry["data"].update(java_release=release, java_version=str(release) + "+")
    entries.append(entry)
    lookup[path] = entry
    added.append(path)


article("linkedlist-null-head", "Java LinkedList null elements: an empty-head ambiguity", "LinkedList permits null elements, so a null result from peekFirst does not prove that the list is empty.", [
    ("Separate absence from payload", ["A work queue that accepts null cannot distinguish an empty queue from a queue whose first work item is null by calling peekFirst alone. Check isEmpty before reading, or reject null at the application's admission boundary.", "getFirst throws on an empty list but returns null when the first stored value is null. That exception is a different contract, not a substitute for explicit input validation. An ArrayDeque rejects null, which removes this particular ambiguity if the application only needs deque operations. See [[java/arraydeque|the ArrayDeque lesson]] before choosing a representation."]),
    ("Keep the invariant near insertion", ["The fixture prints the empty and populated states without conflating them. It removes the null element only after checking membership. A real queue should decide whether null is legal before adding a worker, rather than forcing each consumer to guess what null means."])
], '''import java.util.LinkedList;
public class ReceiptQueueNullBoundary {
    public static void main(String[] args) {
        LinkedList<String> receipts = new LinkedList<>();
        System.out.println("empty=" + receipts.isEmpty() + ", head=" + receipts.peekFirst());
        receipts.addFirst(null);
        System.out.println("empty=" + receipts.isEmpty() + ", head=" + receipts.peekFirst());
        System.out.println("removedNull=" + (receipts.removeFirst() == null));
    }
}''', 'empty=true, head=null\nempty=false, head=null\nremovedNull=true', "Endpoint access is constant time; storing n nodes takes linear memory plus per-node references. Null handling changes the API meaning, not those asymptotic costs.", ["Do not use peekFirst() == null as the sole empty check when null is allowed.", "Do not switch to ArrayDeque while still inserting null.", "Do not hide a null admission policy in each consumer."], ["java/linkedlist", "java/arraydeque", "java/collection-choices"])

article("deque-empty-contracts", "Java Deque empty operations: choose return values or exceptions", "Deque offers endpoint operations that either report an empty container with null or throw NoSuchElementException.", [
    ("Choose one failure shape", ["pollFirst returns null when an empty deque has no head; removeFirst throws. peekFirst and getFirst make the same distinction without removal. Which pair fits the caller depends on whether empty is ordinary control flow or a broken precondition.", "This program uses ArrayDeque, which refuses null members. That makes a null poll result unambiguous. LinkedList can hold null, so a caller using its nullable methods must check emptiness separately. The [[java/linkedlist-null-head|null-head case]] shows the collision."]),
    ("Do not confuse capacity with emptiness", ["offerFirst reports insertion acceptance as a boolean; addFirst may throw when a capacity-constrained deque refuses an insertion. ArrayDeque grows as required, so this example does not exercise a capacity limit. The failure behavior belongs to the implementation and workload, not just the method name."])
], '''import java.util.ArrayDeque;
import java.util.NoSuchElementException;
public class DispatchDequeContracts {
    public static void main(String[] args) {
        ArrayDeque<String> pending = new ArrayDeque<>();
        System.out.println("poll=" + pending.pollFirst());
        try { pending.removeFirst(); }
        catch (NoSuchElementException empty) { System.out.println("remove rejected"); }
        pending.offerLast("receipt-37");
        System.out.println("peek=" + pending.peekFirst());
        System.out.println("take=" + pending.removeFirst());
    }
}''', 'poll=null\nremove rejected\npeek=receipt-37\ntake=receipt-37', "These endpoint calls have amortized constant-time behavior for ArrayDeque. Memory grows with retained elements and backing-array capacity; this example is not a bounded work queue.", ["Do not treat a null poll result as universally unambiguous across implementations.", "Do not handle an empty deque by catching every RuntimeException.", "Do not assume offer means a producer has durable acceptance."], ["java/arraydeque", "java/linkedlist-null-head", "java/blocking-queues"])

article("linkedlist-shallow-copy", "Java LinkedList clone: copied nodes, shared element objects", "LinkedList.clone creates a new list structure while retaining references to the original element objects.", [
    ("Membership and element ownership differ", ["Removing a record from the copy does not remove a node from the original. Changing a mutable record already present in both lists is visible from both. This is a shallow copy, and an ordinary copy constructor has the same element-sharing issue.", "The fixture uses a named InvoiceFlag object so the shared reference is observable. The two collections are distinct, but their first element has the same identity. An immutable element model or deliberate element-copy operation is needed when consumers must not share state."]),
    ("Do not call this a snapshot of a mutable graph", ["Copying n node references costs linear time and additional node storage. It does not copy every object reachable through those references. A process boundary needs serialization rules and schema handling; clone supplies neither. [[java/collection-views|Views and snapshots]] examines the related membership question."])
], '''import java.util.LinkedList;
public class InvoiceFlagCopy {
    static final class InvoiceFlag {
        String state;
        InvoiceFlag(String state) { this.state = state; }
    }
    public static void main(String[] args) {
        LinkedList<InvoiceFlag> original = new LinkedList<>();
        original.add(new InvoiceFlag("queued"));
        LinkedList<InvoiceFlag> copy = (LinkedList<InvoiceFlag>) original.clone();
        copy.getFirst().state = "reviewed";
        System.out.println("shared=" + (original.getFirst() == copy.getFirst()));
        System.out.println("original=" + original.getFirst().state);
        copy.clear();
        System.out.println("sizes=" + original.size() + "," + copy.size());
    }
}''', 'shared=true\noriginal=reviewed\nsizes=1,0', "Cloning a list with n elements costs O(n) time and O(n) new node space. The memory of each referenced element is still shared until the application copies it separately.", ["Do not infer deep copy from distinct list identities.", "Do not expose mutable elements as though an unmodifiable wrapper froze them.", "Do not use clone as a serialization or tenant-isolation boundary."], ["java/linkedlist", "java/collection-views", "java/immutable-collections"])

article("linkedlist-indexed-scan", "Java LinkedList indexed loops: a hidden quadratic traversal", "LinkedList.get(index) walks from the nearer endpoint, so a full indexed loop repeats walks and can take quadratic time.", [
    ("Iteration keeps a moving cursor", ["Both loops in the fixture produce the same receipt sequence. The first calls get for each position; each call can start a new traversal from the head or tail. The second advances one iterator, so the total traversal is linear.", "A tiny list will not reveal this difference in a wall-clock test. The cost follows from the operation contract and traversal pattern; do not publish a fabricated speedup percentage. If random indexing is the requirement, [[java/arraylist|ArrayList]] better matches the access pattern."]),
    ("Keep mutation under the iterator", ["The program only reads. When removing items during traversal, use the iterator's remove method and respect its state rules. Repeated external removals also change positions and can invalidate an iterator. The [[java/linkedlist-cursor|cursor lesson]] covers local edits."])
], '''import java.util.LinkedList;
public class ReceiptScanCost {
    public static void main(String[] args) {
        LinkedList<String> receipts = new LinkedList<>();
        receipts.add("R-71"); receipts.add("R-72"); receipts.add("R-73");
        StringBuilder indexed = new StringBuilder();
        for (int position = 0; position < receipts.size(); position++) indexed.append(receipts.get(position)).append(' ');
        StringBuilder iterated = new StringBuilder();
        for (String receipt : receipts) iterated.append(receipt).append(' ');
        System.out.println(indexed.toString().trim());
        System.out.println(iterated.toString().trim());
    }
}''', 'R-71 R-72 R-73\nR-71 R-72 R-73', "An indexed full scan is O(n²) in the worst and aggregate sense; a single iterator traversal is O(n). Both hold only a constant amount of traversal state apart from output storage.", ["Do not assume List.get has the same cost for every implementation.", "Do not claim timing from a three-item fixture.", "Do not repeatedly obtain listIterator(index) inside a traversal loop."], ["java/linkedlist", "java/arraylist", "java/linkedlist-cursor"])

article("linkedlist-occurrences", "Java LinkedList duplicate removal: first and last occurrence", "LinkedList can remove the first or last equal element, and those choices produce different order-preserving results when duplicates exist.", [
    ("Define which duplicate is retired", ["A receipt feed may contain two events with the same code separated by another event. removeFirstOccurrence removes the earlier one; removeLastOccurrence removes the later one. Neither method is an idempotent record-key policy by itself, because equality may cover fewer fields than the domain's identity.", "Both operations scan to find a match. LinkedList removes a known node cheaply after locating it, but lookup is still linear. A map or set with a stable key is a better fit when repeated membership checks dominate."]),
    ("Check the return value", ["The boolean reports whether an equal value was found and removed. A false result should not be reported as successful cleanup if the caller expected a pending item. The fixture compares the remaining order after each operation."])
], '''import java.util.LinkedList;
import java.util.Arrays;
public class ReceiptDuplicateRetirement {
    public static void main(String[] args) {
        LinkedList<String> events = new LinkedList<>(Arrays.asList("R-9", "R-10", "R-9"));
        System.out.println("first=" + events.removeFirstOccurrence("R-9") + " " + events);
        events.addFirst("R-9");
        System.out.println("last=" + events.removeLastOccurrence("R-9") + " " + events);
        System.out.println("missing=" + events.removeLastOccurrence("R-11"));
    }
}''', 'first=true [R-10, R-9]\nlast=true [R-9, R-10]\nmissing=false', "Each occurrence search takes O(n) time and O(1) auxiliary space; the existing list retains O(n) nodes. The call is not a transactional deduplication operation.", ["Do not ignore a false removal result when absence is an error.", "Do not confuse object equality with a business event identifier.", "Do not sell fast relinking as fast value lookup."], ["java/linkedlist", "java/hashset", "java/hashmap"])

article("list-remove-overloads", "Java List.remove with Integer: index or value", "List.remove(int) removes by position, while List.remove(Object) removes the first equal value.", [
    ("The compile-time argument type selects the overload", ["For List<Integer>, passing the literal 2 calls remove(int), not remove(Object). A queue of numeric receipt codes can silently delete the wrong element if that index exists. Cast to Integer or call Integer.valueOf when the intended operation is value removal.", "The fixture prints both outcomes from separate lists. The first list loses the element at index two. The second loses the element whose value is two. Both operations are legal, which makes this easy to miss during review."]),
    ("Check the representation cost", ["ArrayList shifts later references after removal; LinkedList searches for a matching value and then relinks nodes. Neither representation turns value lookup into constant time. When code needs key-based deletion at scale, a map keyed by the receipt identifier may be the better model."])
], '''import java.util.ArrayList;
import java.util.List;
import java.util.Arrays;
public class NumericReceiptRemoval {
    public static void main(String[] args) {
        List<Integer> byIndex = new ArrayList<>(Arrays.asList(2, 7, 9));
        byIndex.remove(2);
        List<Integer> byValue = new ArrayList<>(Arrays.asList(2, 7, 9));
        byValue.remove(Integer.valueOf(2));
        System.out.println("index=" + byIndex);
        System.out.println("value=" + byValue);
    }
}''', 'index=[2, 7]\nvalue=[7, 9]', "Value removal requires O(n) search in a list. ArrayList index removal may shift O(n) references; a LinkedList positional lookup also traverses O(n) nodes. The overload decision happens at compile time.", ["Do not assume a numeric literal means a numeric value in remove.", "Do not use a cast to change the stored element type accidentally.", "Do not omit the absent-value behavior from an API contract."], ["java/arraylist", "java/linkedlist", "java/hashmap"])

article("synchronized-list-iteration", "Java synchronizedList iteration: hold the wrapper lock", "Collections.synchronizedList serializes individual calls, but a compound iteration still needs a caller-held lock on the wrapper.", [
    ("The lock covers the whole traversal", ["A worker may mutate a shared list between the iterator's next calls even when every individual list operation is synchronized. The caller must synchronize on the returned wrapper while iterating. Synchronizing on the original backing list is a different monitor and does not coordinate with the wrapper.", "The fixture does not start a competing thread. It demonstrates the required monitor placement and a stable sum in a single process; it is not evidence that a production workload avoids contention or starvation."]),
    ("Prefer a clearer ownership model when possible", ["A copied snapshot avoids holding a shared lock during slow processing, but it is stale as soon as the copy finishes and shares mutable element objects. A concurrent queue or a single owning worker may make the application contract easier to reason about. [[java/collection-views|View and snapshot ownership]] covers that distinction."])
], '''import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
public class SharedReceiptBatchRead {
    public static void main(String[] args) {
        List<Integer> amounts = Collections.synchronizedList(new ArrayList<>());
        amounts.add(12); amounts.add(18);
        int total = 0;
        synchronized (amounts) {
            for (int amount : amounts) total += amount;
        }
        System.out.println("total=" + total);
    }
}''', 'total=30', "A full protected traversal is O(n) and keeps the monitor for its duration. Concurrent writers wait for that lock; the code provides mutual exclusion, not parallel read scalability or a durable snapshot.", ["Do not rely on synchronized individual calls to make a multi-call loop atomic.", "Do not lock the unsynchronized backing list instead of the wrapper.", "Do not run blocking network work while holding the list lock."], ["java/linkedlist", "java/iterators", "java/collection-views"])

article("nested-class-ownership", "Java nested classes: instance capture versus static ownership", "A non-static inner class carries an enclosing instance reference; a static nested class has no implicit reference to an outer object.", [
    ("Make retained ownership explicit", ["A dispatch queue holding an inner ReceiptTask also retains its owning DispatchSession. That can keep session state reachable after the request that created it. A static nested task stores only the fields passed to its constructor, so its ownership is visible in the class definition.", "The fixture prints a task from each form. It does not measure heap retention; the reachability consequence follows from the implicit enclosing reference. If the task really needs live session state, passing that dependency deliberately may still be the right design."]),
    ("Package boundaries remain separate", ["Static nested does not mean globally shared or thread-safe. Access modifiers still determine visibility across packages, and a mutable field remains mutable. For an API payload, a top-level or record type may be clearer than either nested form."])
], '''public class DispatchSessionOwnership {
    private final String tenant;
    DispatchSessionOwnership(String tenant) { this.tenant = tenant; }
    final class InnerTask {
        String label() { return tenant + ":inner"; }
    }
    static final class StaticTask {
        private final String tenant;
        StaticTask(String tenant) { this.tenant = tenant; }
        String label() { return tenant + ":static"; }
    }
    public static void main(String[] args) {
        DispatchSessionOwnership session = new DispatchSessionOwnership("east");
        System.out.println(session.new InnerTask().label());
        System.out.println(new StaticTask("west").label());
    }
}''', 'east:inner\nwest:static', "Both task forms have constant-time construction in this fixture. The inner task includes an implicit owner reference, which can extend the owner's lifetime while the task remains reachable.", ["Do not treat static nested as an automatic concurrency guarantee.", "Do not queue an inner object without considering its retained owner.", "Do not confuse package access with nested-class membership."], ["java/classes-objects", "java/records", "spring/bean-scopes"], subject="java")

article("properties-source-order", "Java Properties precedence: merge sources deliberately", "Properties stores string keys and values; application precedence is determined by the order and policy used to combine sources.", [
    ("Choose which source wins", ["This fixture starts with packaged defaults and then overlays a local override. The second putAll wins on duplicate keys. java.util.Properties does not impose a standard deployment precedence between files, environment variables and command-line flags for an application.", "A caller should define and test the priority of each accepted source. In a Spring application the framework has its own property-source ordering, covered by [[spring/profiles-properties|Spring profile and property precedence]]. Do not copy this fixture's order into Spring and assume it overrides Boot's behavior."]),
    ("Validate before starting work", ["The program parses the merged timeout as a number and rejects a nonpositive value. Real services also need bounds, units and a policy for unknown keys. Never print a secret just to prove precedence; this example uses a harmless timeout setting."])
], '''import java.util.Properties;
public class ImportTimeoutConfiguration {
    public static void main(String[] args) {
        Properties defaults = new Properties();
        defaults.setProperty("import.timeout.seconds", "8");
        Properties local = new Properties();
        local.setProperty("import.timeout.seconds", "12");
        Properties effective = new Properties();
        effective.putAll(defaults);
        effective.putAll(local);
        int seconds = Integer.parseInt(effective.getProperty("import.timeout.seconds"));
        if (seconds <= 0 || seconds > 60) throw new IllegalArgumentException("timeout range");
        System.out.println("timeout=" + seconds);
    }
}''', 'timeout=12', "Merging n entries takes O(n) expected map work and retains a new map of O(n) references and strings. Parsing and validation should happen once at startup, not on every request.", ["Do not assume Properties chooses file or environment precedence for you.", "Do not treat a parsed integer as a validated duration.", "Do not log effective secret values during diagnostics."], ["java/classes-objects", "spring/profiles-properties", "spring/configuration-properties"], subject="java")

# Spring additions use tests in the source kit, rather than uncompiled pseudocode.
article("request-scope-proxy", "Spring request scope proxy: resolve state for the current HTTP request", "A request-scoped proxy lets a singleton depend on an object selected from the active web request instead of storing one request's state globally.", [
    ("Inject the proxy, not a captured request", ["The singleton ReceiptLabel reads its tenant from a proxied RequestTenant. The test binds request A and request B in turn, calls the same singleton, and observes different tenant labels. The singleton object identity stays stable while the request target changes.", "Use a method call on the proxy. Direct field access reads a field on the proxy object and can bypass request-target lookup. The proxy does not authenticate either tenant. A production tenant must come from trusted identity and authorization rules, not an untrusted header stored in request scope."]),
    ("No request context means no target", ["After the test clears RequestContextHolder, invoking the proxy throws a ScopeNotActiveException. That is expected for background work without an HTTP request. Capture a narrow authorized value and pass it explicitly to a task instead of retaining a request-scoped proxy in asynchronous work. Compare [[spring/async-boundaries|executor context boundaries]]."])
], '''class RequestTenant {
    private String name;
    void setName(String value) { name = value; }
    String name() { return name; }
}
@Configuration
static class Config {
    @Bean @RequestScope(proxyMode = ScopedProxyMode.TARGET_CLASS)
    RequestTenant requestTenant() { return new RequestTenant(); }
    @Bean ReceiptLabel receiptLabel(RequestTenant tenant) { return new ReceiptLabel(tenant); }
}
record ReceiptLabel(RequestTenant tenant) {
    String text() { return tenant.name(); }
}''', "", "One request target is retained per active request context, plus a singleton proxy. This local test does not measure concurrent traffic, session persistence or authentication; the scope ends with request cleanup.", ["Do not put caller-provided tenant text into a trusted authorization decision.", "Do not call request-scoped targets from a background worker without an explicit context policy.", "Do not assume scoped proxy means the target itself is thread-safe."], ["spring/bean-scopes", "spring/async-boundaries", "spring/method-authorization", "java/thread-local-cleanup"], subject="spring-core", spring=True, proof="RequestScopeBoundaryTest.resolvesASeparateTargetPerBoundRequest")

article("config-override-check", "Spring Boot property override: fail startup on the effective value", "Spring Boot binds an effective configuration value after applying property-source precedence; validation must inspect that selected value before serving requests.", [
    ("Test the actual override", ["The context runner supplies a default timeout and then a higher-priority test value. A bound @ConfigurationProperties bean sees the selected value, not an unordered collection of both strings. The source kit test checks the effective 12-second timeout.", "The second test passes an invalid selected value and expects context startup to fail. This is stronger than checking a private constructor in isolation: the binding and validation path is part of the contract. [[spring/configuration-properties|Binding and validation]] provides the base rules."]),
    ("Precedence and secrecy are separate", ["A value being selected does not make it safe. Bound durations still need range checks; secrets need protected transport, storage and logging policy. This fixture uses a harmless timeout. [[java/properties-source-order|Java Properties]] illustrates a manual merge, whereas this page checks Boot's binding path."])
], '''@ConfigurationProperties("import") @Validated
public record ImportSettings(@Min(1) @Max(60) int timeoutSeconds) {}

new ApplicationContextRunner()
    .withUserConfiguration(SettingsConfig.class)
    .withInitializer(context -> {
        var sources = context.getEnvironment().getPropertySources();
        sources.addLast(new MapPropertySource("packaged-defaults", Map.of("import.timeout-seconds", "8")));
        sources.addFirst(new MapPropertySource("operator-overrides", Map.of("import.timeout-seconds", "12")));
    })
    .run(context -> assertEquals(12,
        context.getBean(ImportSettings.class).timeoutSeconds()));''', "", "Binding happens during context creation, before request handling. This test covers a selected local property pair, not every external file, environment mapping, command-line source or production secret store.", ["Do not assume two sources have equal priority when order matters.", "Do not accept a parsed value without validating its operational range.", "Do not expose effective secrets in an error page or actuator output."], ["spring/configuration-properties", "spring/profiles-properties", "spring/context-testing", "java/properties-source-order"], subject="spring-boot", spring=True, proof="ConfigurationOverrideBoundaryTest.selectsAndValidatesTheEffectiveTimeout")

for subject in {lookup[path]["subject"] for path in added}:
    hub = next(entry for entry in entries if entry["type"] == "subject" and entry["subject"] == subject)
    group = [path for path in added if lookup[path]["subject"] == subject]
    hub["data"]["modules"].append({"title": {"java-collections": "LinkedList contracts under load and mutation", "java": "Nested ownership and application settings", "spring-core": "Request lifetime and scoped dependencies", "spring-boot": "Effective startup configuration"}[subject], "summary": "Check the boundary and follow the related lessons.", "lessons": group})
    hub["updated_at"] = stamp
    if hub["path"].startswith("spring/"):
        links = "<ul>" + "".join('<li><a href="/' + path + '">' + html.escape(lookup[path]["title"]) + "</a></li>" for module in hub["data"]["modules"] for path in module["lessons"]) + "</ul>"
        hub["body"] = re.sub(r"(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)", lambda match: match[1] + links + match[2], hub["body"])

# Extend the established lesson at the exact concept boundary; do not place Spring in Java modules.
reverse = {
    "java/linkedlist": ["java/linkedlist-null-head", "java/linkedlist-shallow-copy", "java/linkedlist-indexed-scan", "java/linkedlist-occurrences"],
    "java/arraydeque": ["java/deque-empty-contracts"],
    "java/arraylist": ["java/list-remove-overloads", "java/linkedlist-indexed-scan"],
    "java/iterators": ["java/synchronized-list-iteration"],
    "java/classes-objects": ["java/nested-class-ownership"],
    "spring/bean-scopes": ["spring/request-scope-proxy"],
    "spring/configuration-properties": ["spring/config-override-check"],
    "spring/profiles-properties": ["spring/config-override-check", "java/properties-source-order"],
}
for path, targets in reverse.items():
    entry = lookup[path]
    marker = "<h2>Next boundary checks</h2>"
    entry["body"] = entry["body"].split(marker)[0] + marker + paragraph("Continue with " + ", ".join(f"[[{target}|{lookup[target]['title']}]]" for target in targets) + ".")
    entry["updated_at"] = stamp

FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"added": added, "count": len(added)}))
