"""Add original Java runtime-discovery and invocation lessons."""
import copy
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
lookup = {row["path"]: row for row in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()

lessons = [
    dict(slug="reflection-target-exception-boundary", title="Java reflection: separate an invoked method failure from lookup failure", group="Reflective invocation", release=17,
         definition="Method.invoke wraps an exception thrown by the invoked method in InvocationTargetException. Lookup and access failures remain separate reflective failures.",
         details="The method looks up one fixed public operation and propagates the policy's RuntimeException as the policy failure. It leaves checked target failures wrapped, so the caller can inspect the cause without silently changing its checked-exception contract. The target class and method must be accessible under Java language and module rules. A string supplied by an untrusted caller should not select arbitrary methods. Cache a Method when the same fixed operation runs repeatedly, while still checking target compatibility.",
         case="A shipment policy throws IllegalStateException while evaluating shipment 47. That is a policy failure, not NoSuchMethodException. Reporting only InvocationTargetException hides the meaningful cause; treating every reflective exception as retryable can repeat a rejected shipment.",
         code='''import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.Objects;

public class ShipmentPolicyInvocation {
    public static String evaluate(Object policy, long shipmentId)
            throws ReflectiveOperationException {
        Objects.requireNonNull(policy);
        Method method = policy.getClass().getMethod("evaluate", long.class);
        try {
            return (String) method.invoke(policy, shipmentId);
        } catch (InvocationTargetException failure) {
            Throwable target = failure.getCause();
            if (target instanceof RuntimeException runtime) throw runtime;
            throw failure;
        }
    }
}''',
         cost="Looking up and invoking a method takes O(1) application space and adds reflective dispatch and boxing overhead to the policy's own work. Repeated lookup can be cached, but the cache must be scoped to class identity and class-loader lifetime.",
         mistakes=["Do not classify a target exception as a missing method or access failure.", "Do not let arbitrary user input name a method to invoke.", "Do not ignore that Method.invoke returns Object and may require a checked cast."],
         related=["java/reflection", "java/reflection-exact-overload-lookup", "java/reflection-trysetaccessible-module"]),
    dict(slug="reflection-exact-overload-lookup", title="Java getMethod: resolve an overload by its exact parameter types", group="Reflective invocation", release=17,
         definition="Class.getMethod selects a public method by name and exact parameter-type array. It does not search for the overload that would be chosen by a normal source-code call.",
         details="The lookup specifies long and int primitives, then invokes a single rate method. A Long.class parameter is not long.class. Method.invoke may box arguments during invocation, but that conversion does not change the method selected during lookup. If the requested signature is absent, NoSuchMethodException signals a contract mismatch; selecting the first method with the right name can silently call a different overload. The sample checks the result type before unboxing it.",
         case="A pricing plugin adds rate(Long, int) beside rate(long, int). Looking up Long.class when the integration contract calls for long.class fails instead of silently choosing a different policy.",
         code='''import java.lang.reflect.Method;
import java.util.Objects;

public class DepotRateLookup {
    public static long cents(Object rateTable, long depotId, int parcelCount)
            throws ReflectiveOperationException {
        Objects.requireNonNull(rateTable);
        Method rate = rateTable.getClass().getMethod("rate", long.class, int.class);
        Object result = rate.invoke(rateTable, depotId, parcelCount);
        if (!(result instanceof Long cents) || cents < 0)
            throw new IllegalStateException("Rate must be nonnegative long cents");
        return cents;
    }
}''',
         cost="Signature lookup and invocation add reflective overhead and O(1) application storage. For a fixed plugin API, validate and cache the selected Method at registration instead of scanning overloads on each request.",
         mistakes=["Do not substitute Long.class for long.class in an exact lookup.", "Do not pick an overload by name alone.", "Do not assume a reflected result has the required type or valid business range."],
         related=["java/reflection-target-exception-boundary", "java/reflection", "java/methodhandle-exact-callsite"]),
    dict(slug="reflection-trysetaccessible-module", title="Java trySetAccessible: handle a denied deep-reflection request", group="Module boundaries", release=11,
         definition="AccessibleObject.trySetAccessible attempts to suppress language access checks and returns false when access cannot be enabled under module boundaries.",
         details="The sample reflects a fixed private auditCode method on an application-owned object. It refuses to invoke when the declaring module does not allow deep reflection to the caller. This operation is appropriate only for a deliberate integration contract; public APIs are preferable. An exported package does not necessarily permit access to private members. If the target belongs to another named module, its package normally needs an opens directive to the caller's module. A failed request must not be worked around by silently depending on runtime flags.",
         case="A plugin updates to a named module and stops opening its internal package. The check rejects the integration clearly rather than assuming setAccessible can override the module boundary.",
         code='''import java.lang.reflect.Method;
import java.util.Objects;

public class AuditCodeAccess {
    public static String read(Object auditRecord) throws ReflectiveOperationException {
        Objects.requireNonNull(auditRecord);
        Method method = auditRecord.getClass().getDeclaredMethod("auditCode");
        if (!method.canAccess(auditRecord) && !method.trySetAccessible())
            throw new IllegalStateException("Audit package is not open to this module");
        return (String) method.invoke(auditRecord);
    }
}''',
         cost="Method lookup, access check, and invocation add O(1) application space with reflective overhead. Reflection does not make module encapsulation free; configuration and compatibility testing are part of this integration cost.",
         mistakes=["Do not assume exports also opens private members.", "Do not ignore a false trySetAccessible result.", "Do not call deep reflection on arbitrary classes supplied by untrusted input."],
         related=["java/module-exports-vs-opens-check", "java/java-modules", "java/reflection-target-exception-boundary"]),
    dict(slug="dynamic-proxy-object-method-contract", title="Java dynamic proxies: define Object-method behavior explicitly", group="Runtime adapters", release=17,
         definition="A java.lang.reflect.Proxy routes interface calls through an InvocationHandler, including equals, hashCode, and toString declared by Object.",
         details="The adapter counts receipt reads and delegates the business call. It implements identity-based equals and hashCode for the proxy itself, and a fixed diagnostic toString. That avoids accidentally forwarding Object calls to an unrelated delegate, recursing through the proxy, or returning a value with the wrong type. A dynamic proxy only implements interfaces; a concrete class cannot be proxied this way. The method handler runs on the caller's thread, so a blocking delegate still blocks that caller.",
         case="A metrics registry inserts a receipt-reader proxy into a hash map. If hashCode returns null or changes with a read count, lookup breaks even though the read method works. This adapter preserves stable identity semantics.",
         code='''import java.lang.reflect.Proxy;
import java.util.Objects;
import java.util.concurrent.atomic.AtomicLong;

public class ReceiptReaderProxy {
    public interface Reader { String read(long receiptId); }

    public static Reader counting(Reader delegate, AtomicLong reads) {
        Objects.requireNonNull(delegate);
        Objects.requireNonNull(reads);
        return (Reader) Proxy.newProxyInstance(
                Reader.class.getClassLoader(), new Class<?>[] { Reader.class },
                (proxy, method, arguments) -> {
                    if (method.getDeclaringClass() == Object.class) {
                        return switch (method.getName()) {
                            case "equals" -> proxy == arguments[0];
                            case "hashCode" -> System.identityHashCode(proxy);
                            case "toString" -> "ReceiptReaderProxy";
                            default -> throw new UnsupportedOperationException(method.getName());
                        };
                    }
                    if (!method.getName().equals("read"))
                        throw new UnsupportedOperationException(method.getName());
                    reads.incrementAndGet();
                    return delegate.read((long) arguments[0]);
                });
    }
}''',
         cost="Each call adds proxy dispatch and an atomic increment before the delegate's work. Storage is O(1) per proxy. A hot call path can make the shared counter contended, so measure it before placing a single counter on every high-volume invocation.",
         mistakes=["Do not forget equals, hashCode, and toString can reach the handler.", "Do not return null for primitive-returning methods such as hashCode.", "Do not expect Proxy to subclass a concrete class or make a blocking delegate asynchronous."],
         related=["java/reflection", "java/threadlocal-context-restoration", "java/service-loader-provider-failure"]),
    dict(slug="service-loader-provider-failure", title="Java ServiceLoader: treat provider discovery as fallible startup work", group="Runtime adapters", release=11,
         definition="ServiceLoader locates implementations registered for a service interface. Iteration can fail when provider metadata, construction, or linkage is broken.",
         details="The loader selects one provider during startup and converts ServiceConfigurationError into a clear configuration failure. It does not silently skip a broken provider, because doing so could change the selected receipt codec. The classpath registration file or named-module provides directive belongs in the deployment artifact; a service interface alone does not register implementations. ServiceLoader lazily discovers and instantiates providers, so moving iteration into a request path can turn a packaging problem into a customer-visible failure. If multiple providers are legal, selection needs an explicit stable policy.",
         case="A deployment lists a provider whose constructor throws. The service fails initialization instead of pretending no codec exists and processing receipts with an unintended fallback.",
         code='''import java.util.Iterator;
import java.util.ServiceConfigurationError;
import java.util.ServiceLoader;

public class ReceiptCodecDiscovery {
    public interface ReceiptCodec { byte[] encode(String receipt); }

    public static ReceiptCodec requiredProvider() {
        try {
            Iterator<ReceiptCodec> providers = ServiceLoader.load(ReceiptCodec.class).iterator();
            if (!providers.hasNext())
                throw new IllegalStateException("No receipt codec registered");
            ReceiptCodec selected = providers.next();
            if (providers.hasNext())
                throw new IllegalStateException("Multiple receipt codecs registered");
            return selected;
        } catch (ServiceConfigurationError broken) {
            throw new IllegalStateException("Receipt codec registration is invalid", broken);
        }
    }
}''',
         cost="Discovery scans P registered providers and instantiates at least those visited, costing O(P) startup time and provider-dependent memory; this sample visits enough to reject a second provider. Holding the selected provider afterward makes per-request discovery cost O(0).",
         mistakes=["Do not expect an interface declaration to register a provider.", "Do not swallow ServiceConfigurationError and select a different provider without policy.", "Do not repeat lazy discovery on every request when providers are deployment configuration."],
         related=["java/java-modules", "java/dynamic-proxy-object-method-contract", "java/classforname-no-initialization"]),
    dict(slug="classforname-no-initialization", title="Java Class.forName: inspect an allowlisted class without initializing it", group="Runtime adapters", release=11,
         definition="Class.forName(name, false, loader) loads and links a class without requesting its initialization. The three-argument form makes loader and initialization policy explicit.",
         details="The method maps a short trusted key to a fixed receipt implementation name, then verifies that the loaded type implements the expected interface. Using arbitrary user text as a class name could load unrelated types or increase attack surface. The false flag avoids initialization during discovery; constructing an instance or using a static member later can still initialize the class. Linkage errors can occur while loading, and loader identity determines whether a class is assignable to this service interface.",
         case="A configuration key names the built-in warehouse codec. The service checks its type at startup without constructing it. A key that is not on the allowlist fails before any class lookup.",
         code='''import java.util.Map;
import java.util.Objects;

public class ReceiptCodecTypeGate {
    public interface ReceiptCodec { byte[] encode(String receipt); }
    public static class WarehouseCodec implements ReceiptCodec {
        public byte[] encode(String receipt) {
            return receipt.getBytes(java.nio.charset.StandardCharsets.UTF_8);
        }
    }

    private static final Map<String, String> ALLOWED = Map.of(
            "warehouse", WarehouseCodec.class.getName());

    public static Class<? extends ReceiptCodec> resolve(String configurationKey)
            throws ClassNotFoundException {
        String className = ALLOWED.get(Objects.requireNonNull(configurationKey));
        if (className == null) throw new IllegalArgumentException("Unknown receipt codec key");
        ClassLoader loader = ReceiptCodecTypeGate.class.getClassLoader();
        return Class.forName(className, false, loader).asSubclass(ReceiptCodec.class);
    }
}''',
         cost="The allowlist lookup is O(1) average for a fixed small map. Class loading and linking may perform I/O and verification once per loader; class initialization is deferred, not removed. Retaining references to classes can retain their defining loader.",
         mistakes=["Do not pass an untrusted class name directly to Class.forName.", "Do not claim false prevents later static initialization.", "Do not assume two classes with the same name but different defining loaders are interchangeable."],
         related=["java/service-loader-provider-failure", "java/reflection", "java/java-modules"]),
    dict(slug="module-exports-vs-opens-check", title="Java modules: distinguish exported APIs from open packages", group="Module boundaries", release=17,
         definition="A named module's exported package supports access to public API types; an open package permits deeper reflection to another module. Module inspection exposes these separate conditions.",
         details="The helper reports whether the provider module exports or opens its class package to a consumer module, and whether the consumer reads the provider. These checks describe module relationships, not whether a particular private member may be invoked; member accessibility, caller context, and lookup mode still matter. Unnamed modules report broad export/open behavior. For a named plugin, declaring exports is not a substitute for opens when a framework needs deep reflection. Code should prefer a public interface if possible and validate module setup at startup.",
         case="A public receipt interface remains callable after a plugin removes opens. A serializer that reads private fields can fail. The report shows that exported and opened are separate deployment decisions.",
         code='''import java.util.Objects;

public class PluginModuleVisibility {
    public record Access(boolean consumerReadsProvider,
                         boolean packageExported, boolean packageOpen) { }

    public static Access inspect(Class<?> providerType, Module consumer) {
        Objects.requireNonNull(providerType);
        Objects.requireNonNull(consumer);
        Module provider = providerType.getModule();
        String packageName = providerType.getPackageName();
        return new Access(consumer.canRead(provider),
                provider.isExported(packageName, consumer),
                provider.isOpen(packageName, consumer));
    }
}''',
         cost="The inspection uses O(1) application data and small module-graph lookups. It is a configuration check, not a performance path; run it when a plugin is registered rather than for each receipt.",
         mistakes=["Do not treat exports as permission for private-member reflection.", "Do not ignore the consumer's readability relationship.", "Do not interpret a package-level report as proof a particular Method or Field is accessible."],
         related=["java/reflection-trysetaccessible-module", "java/java-modules", "java/service-loader-provider-failure"]),
    dict(slug="methodhandle-exact-callsite", title="Java MethodHandle.invokeExact: make the call-site type part of the contract", group="Reflective invocation", release=11,
         definition="MethodHandle.invokeExact requires the call site's argument and return types to match the handle's MethodType exactly; a mismatch raises WrongMethodTypeException.",
         details="The sample caches a public String.substring handle with receiver String and two int arguments. Its cast to String establishes the return type of the invokeExact call site. A Long argument in place of int, or discarding the return value, changes the call-site type and fails; invoke is the adapting form when conversions are deliberate. The handle is resolved once and its lookup obeys access rules. Index validation belongs to the business boundary, not to MethodHandle, so this method checks the requested slice first.",
         case="A receipt code is sliced from index 8 to 10. The result is 47. A refactor that changes one index to long without changing the handle type fails at the exact invocation boundary rather than silently choosing a different overload.",
         code='''import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.MethodType;
import java.util.Objects;

public class ReceiptCodeSlice {
    private static final MethodHandle SLICE = findSlice();

    private static MethodHandle findSlice() {
        try {
            return MethodHandles.publicLookup().findVirtual(String.class,
                    "substring", MethodType.methodType(String.class, int.class, int.class));
        } catch (ReflectiveOperationException failure) {
            throw new ExceptionInInitializerError(failure);
        }
    }

    public static String read(String receiptCode, int start, int end) throws Throwable {
        Objects.requireNonNull(receiptCode);
        if (start < 0 || end < start || end > receiptCode.length())
            throw new IllegalArgumentException("Invalid receipt-code slice");
        return (String) SLICE.invokeExact(receiptCode, start, end);
    }
}''',
         cost="The cached lookup is paid once per class initialization. Each invocation adds method-handle dispatch and substring's O(L) copy for L selected characters, with O(L) new string storage. Wrong call-site types are contract failures, not a fallback lookup mechanism.",
         mistakes=["Do not confuse invokeExact with the adapting invoke call.", "Do not omit the return cast when it defines the expected call-site type.", "Do not assume a handle bypasses public-lookup access rules or input range validation."],
         related=["java/reflection-exact-overload-lookup", "java/varhandles", "java/reflection-target-exception-boundary"]),
]

quiz_path = "quizzes/java-reflection-contracts"
new_paths = ["java/" + lesson["slug"] for lesson in lessons] + [quiz_path]
assert len(new_paths) == len(set(new_paths)) and not set(new_paths) & lookup.keys()
titles = {row["path"]: row["title"] for row in entries}
titles.update({"java/" + lesson["slug"]: lesson["title"] for lesson in lessons})
titles[quiz_path] = "Java runtime discovery contracts quiz"

def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'

def links(paths):
    return "<ul>" + "".join("<li>" + link(path) + "</li>" for path in dict.fromkeys(paths)) + "</ul>"

def related(paths):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(paths)]

new_rows = []
for index, lesson in enumerate(lessons):
    path = "java/" + lesson["slug"]
    cohort = ["java/" + other["slug"] for other in lessons if other["group"] == lesson["group"] and other["slug"] != lesson["slug"]]
    connections = lesson["related"] + cohort + [quiz_path, "java/advanced-java"]
    body = ("<p>" + html.escape(lesson["definition"]) + "</p>"
            + "<h2>Operational contract</h2><p>" + html.escape(lesson["details"]) + "</p>"
            + "<h2>Failure case</h2><p>" + html.escape(lesson["case"]) + "</p>"
            + '<h2>Java code</h2><pre><code class="language-java">' + html.escape(lesson["code"], quote=False) + "</code></pre>"
            + "<h2>Performance and ownership cost</h2><p>" + html.escape(lesson["cost"]) + "</p>"
            + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in lesson["mistakes"]) + "</ul>"
            + "<h2>Connected lessons</h2>" + links(connections))
    row = copy.deepcopy(lookup["java/casts"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), path=path,
               title=lesson["title"], summary=lesson["definition"], body=body,
               subject="java-advanced", category="Programming", tags=["java", lesson["group"].lower(), lesson["slug"]],
               difficulty="Advanced", sort_order=35600 + index * 10, status="published",
               featured=False, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "java/java", "section_path": "java/advanced-java", "kind": "tutorial",
                   "content_format": "html", "reading_minutes": max(5, round(len(re.sub("<[^>]+>", " ", body).split()) / 150)),
                   "author_path": "authors/aitrove-editorial", "related": related(connections), "seo_ready": True,
                   "java_release": lesson["release"], "java_version": str(lesson["release"]) + "+"}
    new_rows.append(row)

questions = [
    ("Where is a target method's thrown exception found after Method.invoke?", "Inside InvocationTargetException", "Inside NoSuchMethodException", "Only in the return value", "The target failure is distinct from lookup and access failures."),
    ("What identifies an overloaded method in Class.getMethod?", "Name and exact parameter classes", "Name only", "Its return value at runtime", "Primitive long.class and wrapper Long.class are different lookup types."),
    ("What does trySetAccessible return when module access cannot be enabled?", "False", "Always true", "The private field value", "A denied deep-reflection request must be handled."),
    ("Which Object methods reach a dynamic proxy handler?", "equals, hashCode, and toString", "Only wait and notify", "No Object methods", "The handler needs consistent identity behavior."),
    ("How can ServiceLoader provider iteration fail?", "ServiceConfigurationError", "Only an empty string", "Only ClassCastException", "Packaging and construction errors can surface during discovery."),
    ("What does false request in three-argument Class.forName?", "Load without requesting initialization", "Never load the class", "Disable linkage checks", "A later use can still initialize the class."),
    ("What does opening a package permit beyond export?", "Deep reflection to allowed modules", "Automatic authentication", "Unlimited memory access", "Exports and opens serve different module contracts."),
    ("What does invokeExact require?", "An exact MethodType match at the call site", "Any widening conversion", "Only a matching method name", "Wrong call-site types raise WrongMethodTypeException."),
]
quiz = copy.deepcopy(lookup["quizzes/java-io"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Check reflective calls, provider discovery, module boundaries, and exact method handles.",
            body="<p>Choose the contract supported by each Java runtime operation.</p><h2>Read the lessons</h2>" + links(new_paths[:-1]) + "<h3>Common Mistakes</h3><p>Do not treat reflective access or provider packaging as implicit.</p>",
            sort_order=35750, status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"].update(content_format="html", subject_root="java/java", section_path="java/java-quizzes", duration_minutes=14, seo_ready=True,
                    questions=[{"prompt": prompt, "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                "answer": (-index) % 3, "explanation": explanation}
                               for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)])
new_rows.append(quiz)

for group in dict.fromkeys(lesson["group"] for lesson in lessons):
    selected = ["java/" + item["slug"] for item in lessons if item["group"] == group]
    hub = lookup["java/advanced-java"]
    hub["data"]["modules"].append({"title": "Runtime: " + group, "summary": "Check invocation, discovery, and module contracts.", "lessons": selected})
    hub["body"] += "<h2>Runtime: " + html.escape(group) + "</h2><p>Inspect the boundaries before invoking or loading.</p>" + links(selected)
    hub["updated_at"] = stamp
lookup["java/java-quizzes"]["data"]["modules"].append({"title": "Runtime discovery contracts", "summary": "Test reflection, proxies, providers, and module access.", "lessons": [quiz_path]})
lookup["java/java-quizzes"]["body"] += "<h2>Runtime discovery contracts</h2><p>Check Java's runtime invocation boundaries.</p>" + links([quiz_path])
lookup["java/java-quizzes"]["updated_at"] = stamp
lookup["java/java"]["body"] += "<h2>Further Java runtime topics</h2><p>Study reflective calls, plugin discovery, module access, and method handles.</p>" + links(new_paths)
lookup["java/java"]["updated_at"] = stamp

backlinks = {
    "java/reflection": ["java/reflection-target-exception-boundary", "java/reflection-exact-overload-lookup", "java/reflection-trysetaccessible-module"],
    "java/java-modules": ["java/module-exports-vs-opens-check", "java/service-loader-provider-failure"],
    "java/varhandles": ["java/methodhandle-exact-callsite"],
    "java/annotation-retention-runtime-gate": ["java/reflection-trysetaccessible-module"],
}
for path, targets in backlinks.items():
    row = lookup[path]
    row["body"] += "<p><strong>Continue with:</strong> " + ", ".join(link(target) for target in targets) + ".</p>"
    row["data"]["related"] = related([item["path"] for item in row["data"].get("related", [])] + targets)
    row["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newArticles": len(lessons), "newQuizzes": 1, "newPaths": new_paths}))
