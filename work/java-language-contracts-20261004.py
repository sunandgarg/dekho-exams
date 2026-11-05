"""Add original Java type-system and language-contract lessons."""

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
lookup = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()

lessons = [
    dict(slug="generic-wildcard-copy-contract", title="Java generic wildcards: copy from a producer into a consumer", group="Generics at API boundaries", release=17,
         definition="An extends wildcard permits reading values as a bound; a super wildcard permits writing values of that bound. A copy method can combine both without claiming two lists have the same element type.",
         details="The source produces ParcelEvent values or a subtype. The destination consumes ParcelEvent values and may be a list of ParcelEvent or Object. The method rejects a source over 47 entries before changing the destination, then appends each element. It does not promise all-or-nothing delivery: a destination that throws during add may already contain a prefix. When atomic publication matters, build a separate immutable result and replace one owner reference instead. The wildcard bounds express allowed operations at compile time; they do not check runtime business rules on each event.",
         case="A depot has a List of ScannedParcel values and needs to add them to a List of ParcelEvent values. List<ScannedParcel> cannot be assigned to List<ParcelEvent>, because that would permit adding a different event subtype to the scanned list. The bounded-copy method accepts the two lists safely while keeping ownership of mutation at the destination.",
         code='''import java.util.List;

public class ParcelEventCopy {
    public interface ParcelEvent { String parcelId(); }
    public record ScannedParcel(String parcelId) implements ParcelEvent { }

    public static <T extends ParcelEvent> void append(
            List<? extends T> source, List<? super T> destination) {
        if (source.size() > 47) throw new IllegalArgumentException("Batch exceeds 47 events");
        for (T event : source) destination.add(event);
    }
}''',
         cost="Reading and appending N elements costs O(N) time and O(1) extra application space. A destination array list may occasionally resize, while a linked destination allocates per entry. The size check is a policy cap, not a rollback mechanism.",
         mistakes=["Do not treat List<Subtype> as a subtype of List<Supertype>.", "Do not assume a wildcard copy is transactional if a destination add fails.", "Do not use a lower-bounded source when the code needs subtype-specific reads."],
         related=["java/generics", "java/collection-views", "java/list-copyof-element-alias"]),
    dict(slug="generic-erasure-runtime-type-check", title="Java type erasure: validate elements with an explicit Class token", group="Generics at API boundaries", release=11,
         definition="Java erases most generic type arguments from runtime class identity. A Class token can validate each element when an unchecked external list crosses into a typed API.",
         details="The method accepts a List<?> from an untyped integration boundary and a requested element class. Class.cast checks each value and creates a fresh List<T>. It rejects null input and null elements before List.copyOf, which itself does not allow null members. The token checks the runtime class of each element; it cannot validate a nested type such as List<String> inside a List<List<String>>. A wire-format parser must still validate field meaning, range, and schema. Two overloads that differ only by List<String> versus List<Long> are illegal because their erased signatures collide.",
         case="A plug-in returns 23 raw receipt values, and the application expects String IDs. The first Long value fails at the boundary with ClassCastException rather than much later inside a billing routine. Calling getClass on the list itself would reveal its implementation class, not its erased element argument.",
         code='''import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

public class TypedReceiptBoundary {
    public static <T> List<T> checkedCopy(List<?> incoming, Class<T> elementType) {
        Objects.requireNonNull(incoming);
        Objects.requireNonNull(elementType);
        if (incoming.size() > 47) throw new IllegalArgumentException("Too many values");
        List<T> checked = new ArrayList<>(incoming.size());
        for (Object value : incoming) checked.add(elementType.cast(value));
        return List.copyOf(checked);
    }
}''',
         cost="Validation and copying take O(N) time and O(N) new list storage for N values, capped at 47. Class.cast checks each runtime element; the one-time copy also prevents later mutations of the incoming list from changing the returned membership.",
         mistakes=["Do not expect a List instance to retain its String or Long type argument at runtime.", "Do not use Class<T> to claim validation of nested generic arguments.", "Do not defer unchecked casts until after data enters domain logic."],
         related=["java/generics", "java/reflection", "java/generic-varargs-boundary"]),
    dict(slug="generic-bridge-method-dispatch", title="Java bridge methods: preserve overrides after generic erasure", group="Generics at API boundaries", release=11,
         definition="A compiler may generate a synthetic bridge method when erasure would otherwise break an overriding method's dispatch signature.",
         details="The base source declares a generic fee method and the concrete source returns Long. At the source level, calling through FeeSource<Long> invokes the concrete override. The compiler can emit an Object-returning bridge alongside the Long-returning method so erased callers still reach that override. Reflection may show both; method scanners should inspect isBridge and isSynthetic before treating every declared method as a separate business API. Do not call the synthetic method directly. An unchecked raw-type call can still move a type error to runtime.",
         case="An audit tool lists methods on a fee provider and reports two rate methods. Only one was written by the developer. The second is a compiler bridge that preserves polymorphism; registering both as separate handlers would double-count one operation.",
         code='''import java.lang.reflect.Method;

public class FeeBridgeInspection {
    static abstract class FeeSource<T> { abstract T rate(); }
    static final class FixedFee extends FeeSource<Long> {
        @Override Long rate() { return 4700L; }
    }

    public static long rateThroughBase() {
        FeeSource<Long> source = new FixedFee();
        return source.rate();
    }

    public static int bridgeCount() {
        int bridges = 0;
        for (Method method : FixedFee.class.getDeclaredMethods()) {
            if (method.isBridge()) bridges++;
        }
        return bridges;
    }
}''',
         cost="The virtual call is ordinary dispatch after compilation. Reflecting over M declared methods costs O(M) time and O(1) application space here, aside from reflection's method objects. Bridge generation is a compatibility detail, not a reason to add runtime casts to correctly typed code.",
         mistakes=["Do not expose compiler bridge methods as separate service endpoints.", "Do not assume generic parameters survive as distinct runtime classes.", "Do not remove an override because reflection shows an extra method."],
         related=["java/generic-erasure-runtime-type-check", "java/reflection", "java/polymorphism"]),
    dict(slug="interface-default-method-conflict", title="Java interface defaults: resolve a two-parent method conflict", group="Dispatch and data contracts", release=11,
         definition="When two unrelated interfaces provide default methods with the same signature, an implementing class must resolve the conflict explicitly.",
         details="The concrete formatter chooses the audit label and receipt label in a fixed order. It calls the two parent defaults with qualified InterfaceName.super syntax, then returns a new label. This decision belongs in the class that combines both contracts. A superclass concrete method can take precedence over interface defaults, so changing a class hierarchy may change dispatch even when interface source remains the same. Default methods add API behavior; they do not replace a review of semantic compatibility between the interfaces.",
         case="A reporting type implements both a receipt naming interface and an audit naming interface. Each supplies label(). Without an override, compilation fails. The explicit result 'AUDIT-82 / RECEIPT-47' makes the combined naming rule visible to callers and reviewers.",
         code='''public class CombinedReceiptLabel {
    interface ReceiptLabel { default String label() { return "RECEIPT-47"; } }
    interface AuditLabel { default String label() { return "AUDIT-82"; } }

    static final class ReportLabel implements ReceiptLabel, AuditLabel {
        @Override public String label() {
            return AuditLabel.super.label() + " / " + ReceiptLabel.super.label();
        }
    }

    public static String render() {
        return new ReportLabel().label();
    }
}''',
         cost="Dispatch and concatenation are constant work for these fixed strings; the returned string allocates storage proportional to its length. The main cost is API governance: every conflict resolution should encode a deliberate business rule rather than blindly pick the first parent.",
         mistakes=["Do not expect Java to select one of two unrelated defaults automatically.", "Do not resolve a conflict with an arbitrary parent when both semantics matter.", "Do not overlook superclass methods when reasoning about inherited behavior."],
         related=["java/interfaces", "java/polymorphism", "java/overload-resolution"]),
    dict(slug="record-compact-constructor-normalization", title="Java compact record constructors: normalize before field assignment", group="Dispatch and data contracts", release=17,
         definition="A compact record constructor receives component parameters and implicitly assigns them to fields after its body completes. It can reject or normalize values before that assignment.",
         details="The sample strips surrounding whitespace from a shipment identifier, rejects a blank value, and limits mass to 47,000 grams. Assigning a new value to the constructor parameter changes what the implicit field assignment stores. The record is only shallowly immutable; if a component holds a mutable collection or array, copy it on entry and control what its accessor returns. Validation in the canonical constructor gives every ordinary construction path the same invariant. Deserialization and reflection still require separate trust considerations.",
         case="A carrier sends '  parcel-82  ' with a mass of 23,000 grams. The stored record ID is 'parcel-82'. A blank ID or 47,001-gram mass fails before a record exists, preventing downstream code from quietly accepting an invalid shipment.",
         code='''public class ShipmentMassPolicy {
    public record ShipmentMass(String shipmentId, int grams) {
        public ShipmentMass {
            if (shipmentId == null) throw new IllegalArgumentException("Missing shipment ID");
            shipmentId = shipmentId.strip();
            if (shipmentId.isBlank() || grams < 0 || grams > 47_000)
                throw new IllegalArgumentException("Invalid shipment mass");
        }
    }

    public static ShipmentMass accept(String id, int grams) {
        return new ShipmentMass(id, grams);
    }
}''',
         cost="strip scans the identifier in O(L) time and may allocate a new string; the numeric checks are O(1). The record stores one reference and one integer. The constructor does not copy a mutable object because these components are a String and a primitive.",
         mistakes=["Do not assign directly to a record component field in a compact constructor.", "Do not call a record deeply immutable when it contains mutable components.", "Do not scatter validation only across selected factory methods."],
         related=["java/records", "java/record-defensive-copy", "java/identifier-policy"]),
    dict(slug="instanceof-pattern-scope", title="Java instanceof patterns: keep a narrowed value inside its valid scope", group="Dispatch and data contracts", release=17,
         definition="An instanceof type pattern tests a reference and binds a narrowed variable only on control-flow paths where the test succeeded.",
         details="The method rejects every value that is not a RefundEvent, including null. After the throwing guard, the compiler knows refund is a RefundEvent for the remaining method body. No explicit cast is needed. Pattern matching does not validate the record's business fields; this code checks the amount separately. This narrow branch is appropriate when an API receives a mixed event type. For a closed set of event kinds, a sealed hierarchy can give stronger compile-time coverage.",
         case="An event router receives an Object representing a refund of 2,300 cents. It returns 2,300. A String or null fails at the routing boundary instead of becoming a zero-value refund, which would hide a bad integration payload.",
         code='''public class RefundPatternGate {
    public record RefundEvent(String receiptId, long cents) { }

    public static long acceptedCents(Object event) {
        if (!(event instanceof RefundEvent refund))
            throw new IllegalArgumentException("Expected refund event");
        if (refund.cents() < 0 || refund.cents() > 47_000)
            throw new IllegalArgumentException("Refund outside policy");
        return refund.cents();
    }
}''',
         cost="The runtime type test and field checks take O(1) time and no collection storage. The pattern variable is a reference to the same object; it is not a copy or a separate validated instance.",
         mistakes=["Do not assume the pattern variable exists on the branch where the test is false.", "Do not treat type matching as validation of record fields.", "Do not map unsupported input to a plausible business value without an explicit rule."],
         related=["java/pattern-switch", "java/sealed-classes", "java/casts"]),
    dict(slug="switch-expression-yield-contract", title="Java switch expressions: return one value from every state", group="Dispatch and data contracts", release=17,
         definition="A switch expression computes a value. Arrow cases avoid statement fall-through, and a block case uses yield to supply its result.",
         details="The enum has three states, and the switch handles each one without a default. Adding a new enum constant makes the source require another case when recompiled, rather than quietly classifying the new state as an old one. The HELD branch uses Math.addExact so an overflow does not produce a negative fee. Passing null still raises a NullPointerException before a case is selected; validate it at the call boundary when null is expected. A switch expression selects a branch; it does not make the arithmetic or state transition atomic with external storage.",
         case="An order has a 2,300-cent base charge. READY keeps it; HELD adds a 47-cent hold fee and returns 2,347; CLOSED returns zero. A fourth state cannot be silently priced by a generic default branch in this source.",
         code='''public class OrderChargeSwitch {
    public enum State { READY, HELD, CLOSED }

    public static long charge(State state, long baseCents) {
        if (baseCents < 0) throw new IllegalArgumentException("Negative charge");
        return switch (state) {
            case READY -> baseCents;
            case HELD -> {
                long holdCharge = Math.addExact(baseCents, 47);
                yield holdCharge;
            }
            case CLOSED -> 0;
        };
    }
}''',
         cost="Branch selection and arithmetic take O(1) time and O(1) extra space. Exhaustive handling is a source-level maintenance property; it does not guarantee that an old compiled binary will understand a newer enum class without recompilation.",
         mistakes=["Do not use break where a block case must yield a value.", "Do not hide a newly introduced enum state behind a permissive default.", "Do not forget overflow or null policy just because the switch is exhaustive."],
         related=["java/control-flow", "java/enums", "java/checked-integer-arithmetic"]),
    dict(slug="sealed-hierarchy-exhaustive-switch", title="Java sealed hierarchies: switch over permitted request kinds", group="Dispatch and data contracts", release=21,
         definition="A sealed interface limits its direct implementations. A pattern switch can then handle the permitted types as an exhaustive set at compile time.",
         details="The sample permits two nested record request kinds and uses a switch expression without a default. If a third permitted kind is added, recompiling this method requires an explicit branch. Both records validate their own values, so each case can work with a constructed domain request. Passing null is not covered by the two type cases and throws at runtime; callers should reject null at intake. Sealing controls direct Java implementations in the same module or package rules; it is not a security boundary for untrusted serialized data.",
         case="An invoicing service handles a ChargeRequest of 2,300 cents or a RefundRequest of 47 cents. If the model later adds a CreditRequest, the switch must be revisited. A fallback that returns zero for every unknown request would conceal a missing billing rule.",
         code='''public class BillingRequestRouter {
    public sealed interface Request permits ChargeRequest, RefundRequest { }
    public record ChargeRequest(long cents) implements Request {
        public ChargeRequest { if (cents < 0) throw new IllegalArgumentException("Negative charge"); }
    }
    public record RefundRequest(long cents) implements Request {
        public RefundRequest { if (cents < 0) throw new IllegalArgumentException("Negative refund"); }
    }

    public static long signedCents(Request request) {
        return switch (request) {
            case ChargeRequest charge -> charge.cents();
            case RefundRequest refund -> Math.negateExact(refund.cents());
        };
    }
}''',
         cost="Type dispatch and checked negation are O(1) work with O(1) extra space. Exhaustiveness reduces omitted-source-branch risk; it does not replace input limits, authorization, or a durable transaction.",
         mistakes=["Do not add a broad default merely to suppress a missing case.", "Do not treat sealed types as validation of wire-format input.", "Do not forget the null boundary when callers can pass null."],
         related=["java/sealed-classes", "java/pattern-switch", "java/instanceof-pattern-scope"]),
    dict(slug="annotation-retention-runtime-gate", title="Java annotation retention: expose metadata without pretending it enforces policy", group="Metadata and constant behavior", release=11,
         definition="A runtime-retained annotation can be read through reflection. Its presence is metadata; application code must still decide and enforce the associated behavior.",
         details="The marker targets methods and remains available at runtime. The lookup selects a method by name and parameter types, avoiding accidental selection of an overload. A true result means the annotation was declared on that method, not that access checks have run. The method handles an absent declaration by throwing NoSuchMethodException to its caller. A policy engine should bind permissions and authentication separately; an annotation alone is not an authorization boundary. Annotation inspection can be cached for stable classes if it sits on a hot request path.",
         case="An invoice handler marks its approve(long) operation for auditing. Reflection finds the marker. The caller must still emit a durable audit record and deny unauthorized callers; an unannotated method should not quietly be treated as approved merely because no marker is present.",
         code='''import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

public class AuditMarkerInspection {
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.METHOD)
    public @interface AuditRequired { }

    public static final class InvoiceActions {
        @AuditRequired public void approve(long invoiceId) { }
    }

    public static boolean marked(Class<?> owner, String methodName,
            Class<?>... parameters) throws NoSuchMethodException {
        return owner.getDeclaredMethod(methodName, parameters)
            .isAnnotationPresent(AuditRequired.class);
    }
}''',
         cost="A reflective lookup scans or indexes class metadata according to the JVM implementation and can allocate Method objects. Treat it as setup work and cache a resolved policy if every request repeats it. Marker presence itself consumes little per-class metadata; the audit action has separate I/O cost.",
         mistakes=["Do not assume an annotation performs its own enforcement.", "Do not inspect by name alone when overloads exist.", "Do not use SOURCE or CLASS retention when runtime reflection must read the marker."],
         related=["java/annotations", "java/reflection", "java/access-control"]),
    dict(slug="repeatable-annotations-runtime-read", title="Java repeatable annotations: read every declared routing label", group="Metadata and constant behavior", release=11,
         definition="A repeatable annotation lets one declaration carry several values of the same annotation type. getAnnotationsByType returns the contained values to runtime code.",
         details="The Label annotation names a container through @Repeatable; both definitions use runtime retention and the same METHOD target. The sample copies the reflected labels into an immutable list of route names. It rejects a method without labels rather than silently treating it as public. The order of labels is the declared container order, but callers should not use annotation order as a priority rule unless that rule is explicit and tested. Route labels are configuration metadata, not proof that the request is allowed to access a route.",
         case="A dispatch method carries labels 'depot-47' and 'depot-82'. A router reads both, then applies its own authorization and conflict rules. Reading only getAnnotation(Label.class) may miss the intended repeated values when a container is present.",
         code='''import java.lang.annotation.ElementType;
import java.lang.annotation.Repeatable;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;

public class DispatchLabelReader {
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.METHOD)
    @Repeatable(Labels.class)
    public @interface Label { String value(); }

    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.METHOD)
    public @interface Labels { Label[] value(); }

    @Label("depot-47") @Label("depot-82")
    public void dispatch() { }

    public static List<String> labels(Method method) {
        Label[] declared = method.getAnnotationsByType(Label.class);
        if (declared.length == 0) throw new IllegalArgumentException("No route labels");
        List<String> names = new ArrayList<>(declared.length);
        for (Label label : declared) names.add(label.value());
        return List.copyOf(names);
    }
}''',
         cost="Reflection returns R annotation values, and copying their strings costs O(R) time and O(R) list storage. Annotation lookups in a hot route should be resolved once at startup, while per-request authorization still uses current security state.",
         mistakes=["Do not query a repeated annotation as if only one instance can exist.", "Do not give the container a different target or retention contract.", "Do not treat labels as access-control decisions."],
         related=["java/annotation-retention-runtime-gate", "java/annotations", "java/reflection"]),
    dict(slug="enum-constant-specific-fee", title="Java enum constant bodies: keep each fee rule with its tier", group="Metadata and constant behavior", release=11,
         definition="An enum constant can provide its own implementation of an abstract method. This binds a finite set of named choices to distinct behavior without string-based branching elsewhere.",
         details="The tier validates parcel grams at the method entry, then each constant computes its own fee with checked arithmetic. The formulas are policy examples: STANDARD charges 47 cents per kilogram rounded up, and EXPRESS charges 82 cents per kilogram rounded up. The result of 1,001 grams is two kilograms by policy. Enum constants are singletons, so do not place mutable per-request state inside a constant body. Adding a tier still requires a business review of callers and persisted names.",
         case="A 1,001-gram parcel costs 94 cents at STANDARD or 164 cents at EXPRESS. If fees change, the code review can see the two named policies separately. The method rejects negative or over-47,000-gram inputs before pricing.",
         code='''public class ParcelTierFees {
    public enum Tier {
        STANDARD { @Override long centsPerKilogram() { return 47; } },
        EXPRESS { @Override long centsPerKilogram() { return 82; } };

        abstract long centsPerKilogram();

        public long fee(int grams) {
            if (grams < 0 || grams > 47_000)
                throw new IllegalArgumentException("Mass outside policy");
            long kilograms = (grams + 999L) / 1_000L;
            return Math.multiplyExact(kilograms, centsPerKilogram());
        }
    }
}''',
         cost="Selection, integer rounding, and multiplication are O(1) time with O(1) extra space. The enum instances are initialized once. The 47,000-gram cap bounds the result here, while multiplyExact keeps later policy changes from silently overflowing.",
         mistakes=["Do not store mutable request data on a shared enum constant.", "Do not divide before adding the rounding offset when the policy requires ceiling.", "Do not persist enum names as an unreviewed long-term compatibility contract."],
         related=["java/enums", "java/switch-expression-yield-contract", "java/checked-integer-arithmetic"]),
]

quiz_path = "quizzes/java-language-contracts"
quiz_title = "Java generics and language contracts quiz"
new_paths = ["java/" + lesson["slug"] for lesson in lessons] + [quiz_path]
assert len(new_paths) == len(set(new_paths)) and not set(new_paths) & lookup.keys()
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({"java/" + lesson["slug"]: lesson["title"] for lesson in lessons})
titles[quiz_path] = quiz_title


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
    cohort = ["java/" + other["slug"] for other in lessons
              if other["group"] == lesson["group"] and other["slug"] != lesson["slug"]]
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
               difficulty="Advanced", sort_order=35000 + index * 10, status="published",
               featured=False, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "java/java", "section_path": "java/advanced-java",
                   "kind": "tutorial", "content_format": "html", "reading_minutes": max(5, round(len(re.sub("<[^>]+>", " ", body).split()) / 150)),
                   "author_path": "authors/aitrove-editorial", "related": related(connections),
                   "seo_ready": True, "java_release": lesson["release"], "java_version": str(lesson["release"]) + "+"}
    new_rows.append(row)

questions = [
    ("Which wildcard bound lets a list receive values of T?", "List<? super T>", "List<? extends T>", "List<T[]> only", "A lower bound accepts writes of T while preserving the destination's possible supertype."),
    ("What does Class<T>.cast validate in a List<?> copy?", "Each runtime element against the supplied class", "Nested generic arguments automatically", "The list's erased type parameter", "Erasure removes most element-argument identity from the list object."),
    ("Why can reflection show a bridge method?", "The compiler preserves an override after erasure", "The source declares two handlers", "The JVM duplicates every public method", "A synthetic bridge can preserve polymorphic dispatch."),
    ("What must a class do when unrelated interfaces provide the same default method?", "Override and resolve the conflict", "Rely on the first interface listed", "Call both automatically", "The inherited defaults have an unresolved behavioral conflict."),
    ("When does a compact record constructor assign component fields?", "After its body completes normally", "Before validation starts", "Only when a factory method calls it", "Its parameters can be normalized before implicit assignment."),
    ("When is an instanceof pattern variable usable after a guard?", "On paths where matching succeeded", "On both true and false branches", "Only before the type test", "Flow-scoped binding follows the successful pattern result."),
    ("How does a switch expression block produce its value?", "With yield", "With break", "With fall-through", "A block case yields a result to the enclosing expression."),
    ("What does a sealed pattern switch gain when all permitted kinds are covered?", "A source-level exhaustiveness check", "Authorization of incoming bytes", "Automatic null handling", "The compiler can require another branch when the hierarchy changes."),
    ("Does a runtime-retained audit annotation perform the audit itself?", "No, application code must enforce it", "Yes, reflection writes records", "Yes, the JVM denies calls", "Metadata describes a policy; it does not implement it."),
    ("How should repeated annotations be read as a group?", "getAnnotationsByType", "Only getAnnotation once", "Only getClass", "The repeatable container can hold multiple values."),
    ("Where does constant-specific enum behavior live?", "In each named constant's body", "In mutable per-request enum fields", "Only in a string switch elsewhere", "An enum constant can implement an abstract method."),
]
quiz = copy.deepcopy(lookup["quizzes/java-io"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + quiz_path)), path=quiz_path,
            title=quiz_title, summary="Check generics, dispatch, records, pattern matching, and runtime metadata.",
            body="<p>Choose the decision supported by each Java type or language contract.</p><h2>Read the lessons</h2>" + links(new_paths[:-1]) + "<h3>Common Mistakes</h3><p>Do not mistake compile-time type coverage or metadata for runtime authorization.</p>",
            sort_order=35150, status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"].update(content_format="html", subject_root="java/java", section_path="java/java-quizzes",
                    duration_minutes=18, seo_ready=True,
                    questions=[{"prompt": prompt,
                                "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                "answer": (-index) % 3, "explanation": explanation}
                               for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)])
new_rows.append(quiz)

for group in dict.fromkeys(lesson["group"] for lesson in lessons):
    selected = ["java/" + item["slug"] for item in lessons if item["group"] == group]
    hub = lookup["java/advanced-java"]
    hub["data"]["modules"].append({"title": group, "summary": "Keep type, dispatch, and metadata contracts explicit.", "lessons": selected})
    hub["body"] += "<h2>" + html.escape(group) + "</h2><p>Read the runtime boundary behind each language feature.</p>" + links(selected)
    hub["updated_at"] = stamp
lookup["java/java-quizzes"]["data"]["modules"].append({"title": "Generics and language contracts", "summary": "Test type and dispatch decisions.", "lessons": [quiz_path]})
lookup["java/java-quizzes"]["body"] += "<h2>Generics and language contracts</h2><p>Check the new language contracts.</p>" + links([quiz_path])
lookup["java/java-quizzes"]["updated_at"] = stamp
lookup["java/java"]["body"] += "<h2>Further Java language topics</h2><p>Study generics, dispatch, records, and metadata at runtime.</p>" + links(new_paths)
lookup["java/java"]["updated_at"] = stamp

backlinks = {
    "java/generics": ["java/generic-wildcard-copy-contract", "java/generic-erasure-runtime-type-check", "java/generic-bridge-method-dispatch"],
    "java/interfaces": ["java/interface-default-method-conflict"],
    "java/records": ["java/record-compact-constructor-normalization"],
    "java/pattern-switch": ["java/instanceof-pattern-scope", "java/sealed-hierarchy-exhaustive-switch"],
    "java/sealed-classes": ["java/sealed-hierarchy-exhaustive-switch"],
    "java/annotations": ["java/annotation-retention-runtime-gate", "java/repeatable-annotations-runtime-read"],
    "java/enums": ["java/enum-constant-specific-fee", "java/switch-expression-yield-contract"],
    "java/reflection": ["java/generic-bridge-method-dispatch", "java/annotation-retention-runtime-gate"],
}
for old_path, targets in backlinks.items():
    old = lookup[old_path]
    old["body"] += "<p><strong>Continue with:</strong> " + ", ".join(link(target) for target in targets) + ".</p>"
    old["data"]["related"] = related([item["path"] for item in old["data"].get("related", [])] + targets)
    old["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newArticles": len(lessons), "newQuizzes": 1, "newPaths": new_paths}))
