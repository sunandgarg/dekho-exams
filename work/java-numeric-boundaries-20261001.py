"""Add original Java numeric boundary lessons with executable examples."""

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


def add(slug, title, definition, sections, source, output, cost, mistakes, related, release=8):
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
        ", ".join("[[" + item + "|" + lookup.get(item, {}).get("title", item.rsplit("/", 1)[-1].replace("-", " ")) + "]]" for item in related) + "."
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
        tags=["java", "numeric", slug],
        difficulty="Intermediate",
        sort_order=1100 + len(added),
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
        "java_release": release,
        "java_version": str(release) + "+",
    }
    entry["_related_paths"] = related
    entries.append(entry)
    lookup[path] = entry
    added.append(path)


add(
    "math-abs-min-value",
    "Java Math.abs on Integer.MIN_VALUE: detect the one value that cannot turn positive",
    "Math.abs(int) cannot represent the positive magnitude of Integer.MIN_VALUE, so that input remains negative.",
    [
        ("Validate before using magnitude", [
            "The int range contains one more negative value than positive values. A partition key or distance calculation that assumes Math.abs always returns nonnegative can produce an invalid index at this boundary. Java 15 adds Math.absExact, which throws instead of returning the wrapped result.",
            "The fixture prints the surprising value, then rejects it with absExact. On older releases, widen to long before taking the absolute value. [[java/checked-integer-arithmetic|Checked arithmetic]] covers the same range principle for addition."
        ]),
        ("Do not repair an overflow afterward", [
            "Once an int result has wrapped, casting that result to long does not restore the lost positive magnitude. Widen the operand before the operation or use the exact method."
        ]),
    ],
    '''public class PartitionMagnitudeGate {
    public static void main(String[] args) {
        int partitionDelta = Integer.MIN_VALUE;
        System.out.println(Math.abs(partitionDelta));
        try { Math.absExact(partitionDelta); }
        catch (ArithmeticException rejected) { System.out.println("magnitude overflow rejected"); }
        System.out.println(Math.abs((long) partitionDelta));
    }
}''',
    "-2147483648\nmagnitude overflow rejected\n2147483648",
    "Each calculation uses constant time and storage. The failure is a representation limit, not a performance issue. Choose a wider result type when the full mathematical magnitude is required.",
    ["Do not assume Math.abs(int) is always nonnegative.", "Do not cast the already-wrapped int result to long.", "Do not call Math.absExact from a Java 8 compilation target."],
    ["java/checked-integer-arithmetic", "java/operators", "java/biginteger-exact-conversion", "java/floor-div-mod-negative"],
    15,
)


add(
    "floor-div-mod-negative",
    "Java floorDiv and floorMod: assign negative coordinates to stable buckets",
    "Java integer division truncates toward zero, while Math.floorDiv rounds toward negative infinity and floorMod uses the corresponding nonnegative remainder for a positive divisor.",
    [
        ("Choose the bucket rule", [
            "A coordinate of -7 with bucket width 3 belongs in bucket -3 when buckets cover [-9,-6), [-6,-3), and so on. Plain -7 / 3 yields -2; floorDiv yields -3, and floorMod supplies offset 2 inside that bucket. The quotient and remainder must come from the same convention.",
            "[[java/operators|Operator rules]] explain truncating division. The fixture prints both conventions so an index mapping can be checked before it reaches a data structure."
        ]),
        ("Guard the divisor", [
            "A zero width throws ArithmeticException. A negative divisor changes the sign policy for the remainder, so this bucket contract requires a positive width. Also consider the MIN_VALUE divided by -1 overflow case for unrestricted signed inputs."
        ]),
    ],
    '''public class WarehouseGridBucket {
    public static void main(String[] args) {
        int coordinate = -7;
        int width = 3;
        System.out.println("truncated=" + coordinate / width + ":" + coordinate % width);
        System.out.println("floored=" + Math.floorDiv(coordinate, width) + ":" + Math.floorMod(coordinate, width));
    }
}''',
    "truncated=-2:-1\nfloored=-3:2",
    "Both mappings use constant work and storage. The choice affects key distribution and lookup correctness; changing it after writing persistent bucket IDs requires a migration.",
    ["Do not mix truncating division with floorMod.", "Do not assume the % result is nonnegative for a negative dividend.", "Do not accept a zero or negative bucket width under this contract."],
    ["java/operators", "java/math-abs-min-value", "java/checked-integer-arithmetic", "java/arrays"],
)


add(
    "bigdecimal-divide-rounding",
    "Java BigDecimal.divide: make nonterminating quotients explicit",
    "BigDecimal.divide without a rounding policy throws when the exact decimal quotient does not terminate.",
    [
        ("Declare scale at the boundary", [
            "One unit split among three recipients has no finite decimal representation. A financial allocation must choose a scale and rounding mode, then decide how any remainder is assigned. Catching the exception and inventing a default amount would hide that policy.",
            "The fixture rejects exact one-third division and then prints a two-decimal HALF_EVEN result. [[java/bigdecimal|BigDecimal fundamentals]] cover text construction; [[java/bigdecimal-setscale-unnecessary|UNNECESSARY rounding]] is useful when truncation must be rejected."
        ]),
        ("Reconcile the total", [
            "Three independently rounded shares of 0.33 add to 0.99, not 1.00. For money, allocate the remaining minor unit by an explicit rule rather than pretending the rounded quotient conserves the total."
        ]),
    ],
    '''import java.math.BigDecimal;
import java.math.RoundingMode;

public class SettlementSharePolicy {
    public static void main(String[] args) {
        BigDecimal settlement = new BigDecimal("1.00");
        BigDecimal recipients = new BigDecimal("3");
        try { settlement.divide(recipients); }
        catch (ArithmeticException rejected) { System.out.println("exact quotient unavailable"); }
        BigDecimal share = settlement.divide(recipients, 2, RoundingMode.HALF_EVEN);
        System.out.println("share=" + share);
        System.out.println("allocated=" + share.multiply(recipients));
    }
}''',
    "exact quotient unavailable\nshare=0.33\nallocated=0.99",
    "BigDecimal arithmetic allocates immutable results whose cost grows with operand precision. This small fixture is cheap; the material risk is losing a minor unit unless the allocation algorithm reconciles the rounded shares.",
    ["Do not call divide without a rounding policy for arbitrary ratios.", "Do not assume independently rounded shares sum to the original amount.", "Do not construct a declared decimal amount from an imprecise double."],
    ["java/bigdecimal", "java/bigdecimal-setscale-unnecessary", "java/bigdecimal-scale-equality", "java/decimal-parse-boundary"],
)


add(
    "bigdecimal-setscale-unnecessary",
    "Java RoundingMode.UNNECESSARY: reject hidden fractional cents",
    "BigDecimal.setScale with RoundingMode.UNNECESSARY succeeds only when the requested scale can represent the value exactly.",
    [
        ("Validate a money input before posting", [
            "A two-decimal currency field can accept 47.00 but should reject 47.005 if the API forbids rounding at ingestion. UNNECESSARY turns that rule into an exception instead of silently moving value. Apply it before persisting or publishing a ledger entry.",
            "[[java/bigdecimal-divide-rounding|Division]] may need an explicit rounding policy when shares are calculated. In contrast, validation of an externally supplied amount can require exact two-decimal representation. These are different boundaries."
        ]),
        ("Keep representation policy deliberate", [
            "Scale is part of BigDecimal.equals. After validation, normalize the stored scale if the database or equality policy expects one representation. [[java/bigdecimal-scale-equality|Scale equality]] explains why equal numeric values can still behave differently as keys."
        ]),
    ],
    '''import java.math.BigDecimal;
import java.math.RoundingMode;

public class LedgerAmountScaleGate {
    static BigDecimal cents(String input) {
        return new BigDecimal(input).setScale(2, RoundingMode.UNNECESSARY);
    }

    public static void main(String[] args) {
        System.out.println(cents("47.00"));
        try { cents("47.005"); }
        catch (ArithmeticException rejected) { System.out.println("fractional cent rejected"); }
    }
}''',
    "47.00\nfractional cent rejected",
    "Parsing and scaling allocate BigDecimal values proportional to the input's digits. Cap input length before parsing untrusted text. An exception is a validation signal here; it should be translated into a field-level error at the request boundary.",
    ["Do not round an input that the contract requires to be exact.", "Do not treat scale validation as a substitute for input-length limits.", "Do not use BigDecimal.equals as numeric equality without considering scale."],
    ["java/bigdecimal", "java/bigdecimal-divide-rounding", "java/bigdecimal-scale-equality", "java/decimal-parse-boundary"],
)


add(
    "biginteger-exact-conversion",
    "Java BigInteger.intValueExact: reject a narrowing conversion",
    "BigInteger.intValue keeps only low-order bits when a value is out of int range, while intValueExact rejects the conversion.",
    [
        ("Validate the storage width", [
            "A wide external sequence number can parse correctly and still fail when stored in an int field. Silent narrowing can collide with an existing ID. The fixture uses 4294967297, whose low 32 bits equal one, to make the collision visible.",
            "Call intValueExact when the target schema requires int, or keep the BigInteger through the workflow. [[java/unsigned-integer-parsing|Unsigned int parsing]] has a different representation contract: it interprets all 32 bits as an unsigned value, but still cannot hold an arbitrary BigInteger."
        ]),
        ("Reject before mutation", [
            "Convert and validate before inserting into a map or database. A failed exact conversion should not leave a partially updated record. [[java/checked-integer-arithmetic|Checked arithmetic]] addresses overflow during computation, not just narrowing."
        ]),
    ],
    '''import java.math.BigInteger;

public class ExternalSequenceWidthGate {
    public static void main(String[] args) {
        BigInteger externalId = new BigInteger("4294967297");
        System.out.println("narrowed=" + externalId.intValue());
        try { externalId.intValueExact(); }
        catch (ArithmeticException rejected) { System.out.println("int range rejected"); }
    }
}''',
    "narrowed=1\nint range rejected",
    "The conversion itself is small, but parsing an arbitrarily long integer consumes memory and CPU proportional to its digits. Bound the input length. Losing high bits is a correctness fault, not a useful optimization.",
    ["Do not use intValue for an externally assigned unique identifier without a range check.", "Do not assume a parsed BigInteger fits the next storage type.", "Do not confuse unsigned 32-bit interpretation with arbitrary precision."],
    ["java/checked-integer-arithmetic", "java/unsigned-integer-parsing", "java/long-to-double-precision", "java/math-abs-min-value"],
)


add(
    "double-nan-collection-contracts",
    "Java Double NaN and signed zero: primitive and wrapper comparisons differ",
    "Primitive double comparisons and Double wrapper equality use different rules for NaN and signed zero.",
    [
        ("Know which equality a collection uses", [
            "At the primitive level NaN is unequal to itself, while Double.equals treats canonical NaN values as equal. A HashSet of boxed doubles therefore holds one NaN key. Signed positive and negative zero compare equal with ==, but Double.equals distinguishes them. This matters for keyed metrics and deduplication.",
            "The fixture prints both cases. [[java/double-finite-validation|Finite-value validation]] can reject NaN before it reaches a map or arithmetic pipeline when the domain has no meaning for it."
        ]),
        ("Define a metric-key policy", [
            "If zero signs should collapse, normalize them before using Double as a key. If NaN is invalid input, reject it rather than relying on wrapper equality. A comparator and equals policy must also agree with the collection being used."
        ]),
    ],
    '''import java.util.HashSet;
import java.util.Set;

public class SensorReadingIdentity {
    public static void main(String[] args) {
        double missingReading = Double.NaN;
        System.out.println("primitive NaN=" + (missingReading == missingReading));
        Set<Double> unique = new HashSet<>();
        unique.add(Double.NaN);
        unique.add(Double.NaN);
        System.out.println("boxed NaN count=" + unique.size());
        System.out.println("primitive zero=" + (-0.0 == 0.0));
        System.out.println("boxed zero=" + Double.valueOf(-0.0).equals(0.0));
    }
}''',
    "primitive NaN=false\nboxed NaN count=1\nprimitive zero=true\nboxed zero=false",
    "Each comparison is constant work. HashSet adds storage for boxed keys, and its identity semantics follow Double.equals rather than primitive ==. The correct policy depends on whether signed zero and NaN carry domain meaning.",
    ["Do not assume boxed Double equality matches primitive == for NaN or signed zero.", "Do not store NaN as a normal measurement if the domain requires finite values.", "Do not use floating-point keys without defining normalization."],
    ["java/double-finite-validation", "java/hashset", "java/comparator-contracts", "java/floating-sum-order"],
)


add(
    "double-finite-validation",
    "Java Double.isFinite: reject Infinity and NaN at input boundaries",
    "Double.parseDouble accepts special non-finite values and can overflow to Infinity, so a numeric measurement parser should validate finiteness explicitly.",
    [
        ("Reject invalid measurements early", [
            "A sensor API that expects a physical reading should not accept NaN or Infinity as an ordinary quantity. A huge exponent such as 1e400 parses to Infinity rather than throwing a range error. Double.isFinite catches both that result and explicit NaN input.",
            "The fixture accepts 47.5 and rejects two non-finite strings. [[java/double-nan-collection-contracts|NaN key behavior]] explains why passing these values onward can affect collection semantics."
        ]),
        ("Separate finiteness from range", [
            "A finite value can still exceed the sensor's allowed physical range. Check both conditions at the request boundary. For exact decimal money, use [[java/bigdecimal|BigDecimal]] with its own scale and precision policy rather than double."
        ]),
    ],
    '''public class SensorReadingGate {
    static double parse(String raw) {
        double reading = Double.parseDouble(raw);
        if (!Double.isFinite(reading)) throw new IllegalArgumentException("non-finite reading");
        return reading;
    }

    public static void main(String[] args) {
        System.out.println(parse("47.5"));
        for (String raw : new String[] {"1e400", "NaN"}) {
            try { parse(raw); }
            catch (IllegalArgumentException rejected) { System.out.println(rejected.getMessage()); }
        }
    }
}''',
    "47.5\nnon-finite reading\nnon-finite reading",
    "Parsing work grows with input length, so cap the field size before conversion. The finite check is constant work and does not replace domain range validation or an exact-decimal policy.",
    ["Do not assume parseDouble rejects an overflowing exponent.", "Do not let NaN pass a normal measurement validation path.", "Do not use finiteness as the only range check."],
    ["java/double-nan-collection-contracts", "java/floating-sum-order", "java/bigdecimal", "java/decimal-parse-boundary"],
)


add(
    "floating-sum-order",
    "Java floating-point sums: input order can change the result",
    "double addition rounds after each operation, so regrouping the same finite inputs can change the computed sum.",
    [
        ("Make aggregation requirements explicit", [
            "A very large reading can absorb a much smaller one. When the large positive and negative values cancel later, the absorbed unit does not return. The fixture sums the same three values in two orders and gets zero or one. An exact decimal reference shows the intended total for this particular input.",
            "A compensated summation algorithm can reduce error for many datasets, but it is not an exact-money representation. [[java/bigdecimal|BigDecimal]] is appropriate when decimal units are contractual; [[java/double-finite-validation|finite checks]] should precede any double aggregation."
        ]),
        ("Avoid accidental order contracts", [
            "Parallel reductions may combine partitions in different orders. If reports must be bitwise reproducible, define a stable order or use an exact accumulator with a bounded scale and range. Document the accepted error if approximate science data remains in double."
        ]),
    ],
    '''import java.math.BigDecimal;

public class SensorAggregateOrder {
    static double sum(double[] readings) {
        double total = 0;
        for (double reading : readings) total += reading;
        return total;
    }

    public static void main(String[] args) {
        System.out.println(sum(new double[] {1e16, 1.0, -1e16}));
        System.out.println(sum(new double[] {1e16, -1e16, 1.0}));
        BigDecimal exact = new BigDecimal("10000000000000000")
                .add(BigDecimal.ONE)
                .subtract(new BigDecimal("10000000000000000"));
        System.out.println(exact.toPlainString());
    }
}''',
    "0.0\n1.0\n1",
    "Each double pass is O(n) time and O(1) extra storage. BigDecimal uses space and work that grow with precision. Neither ordering trick nor one sample output proves a general error bound for an arbitrary dataset.",
    ["Do not assume addition is associative for double.", "Do not compare approximate aggregates as if their low bits were contractual.", "Do not convert binary doubles to decimal after precision has already been lost and expect recovery."],
    ["java/double-finite-validation", "java/double-nan-collection-contracts", "java/bigdecimal", "java/streams"],
)


add(
    "unsigned-integer-parsing",
    "Java unsigned int parsing: preserve 32-bit protocol values",
    "Integer.parseUnsignedInt accepts decimal values through 2^32-1 but stores the bits in a signed int, so ordinary printing can appear negative.",
    [
        ("Keep the protocol interpretation", [
            "A device counter may use every bit of a 32-bit unsigned field. The maximum value parses into an int with all bits set, which prints as -1 under signed formatting. Convert with Integer.toUnsignedLong or toUnsignedString before display or arithmetic that expects the unsigned value.",
            "The fixture prints all three views of one field. [[java/biginteger-exact-conversion|Exact narrowing]] applies when an external number must actually fit a signed int; it is not the same as retaining an unsigned bit pattern."
        ]),
        ("Reject values outside the field width", [
            "An input larger than 2^32-1 fails parsing. Do not strip the sign or cast from long without checking the protocol width; that would silently wrap a different value into the field."
        ]),
    ],
    '''public class DeviceSequenceBits {
    public static void main(String[] args) {
        int encoded = Integer.parseUnsignedInt("4294967295");
        System.out.println("signed=" + encoded);
        System.out.println("unsigned=" + Integer.toUnsignedLong(encoded));
        System.out.println("text=" + Integer.toUnsignedString(encoded));
    }
}''',
    "signed=-1\nunsigned=4294967295\ntext=4294967295",
    "The conversions use fixed-width primitive storage. Parsing cost grows with input length, so bound the field before conversion. A signed int can store the bits, but its ordinary operators and formatting need deliberate unsigned handling.",
    ["Do not interpret the signed printout as the unsigned protocol value.", "Do not cast an unchecked long into an unsigned 32-bit field.", "Do not confuse bit preservation with signed numeric range validation."],
    ["java/biginteger-exact-conversion", "java/operators", "java/checked-integer-arithmetic", "java/bytebuffer-order"],
)


add(
    "long-to-double-precision",
    "Java long to double: large integer IDs can lose unit precision",
    "A double has finite significand precision, so converting a sufficiently large long can round away its final integer units.",
    [
        ("Keep identifiers integral", [
            "The first integer above 2^53 cannot be represented exactly as a double. The fixture converts 9007199254740993 to double and then back to long; it becomes 9007199254740992. A JSON or analytics pipeline that routes IDs through double can merge two distinct values.",
            "Store identifiers as long, BigInteger, or validated text through boundaries that promise exactness. [[java/biginteger-exact-conversion|Exact integer narrowing]] catches range loss; this page addresses precision loss even though double has a much wider magnitude range."
        ]),
        ("Separate measurement from identity", [
            "Approximate floating-point values can be appropriate for measurements with an error budget. They are a poor intermediate type for ledger sequence numbers, counters that must increment by one, or keys that must round-trip exactly."
        ]),
    ],
    '''public class LedgerSequencePrecision {
    public static void main(String[] args) {
        long sequence = 9007199254740993L;
        double approximate = sequence;
        long roundTrip = (long) approximate;
        System.out.println(roundTrip);
        System.out.println("same=" + (sequence == roundTrip));
    }
}''',
    "9007199254740992\nsame=false",
    "The casts are constant work and storage. The lost unit cannot be restored by casting back; validation must happen before a lossy numeric serialization or transformation.",
    ["Do not pass large integer IDs through double-based storage or APIs without an exactness check.", "Do not assume a wide magnitude range implies unit precision.", "Do not use a round-trip cast as a repair after precision was lost."],
    ["java/biginteger-exact-conversion", "java/floating-sum-order", "java/checked-integer-arithmetic", "java/operators"],
)


for path in added:
    entry = lookup[path]
    entry["data"]["related"] = [
        {"path": target, "title": lookup[target]["title"]}
        for target in entry.pop("_related_paths")
    ]

hub = lookup["java/java"]
title = "Numeric representation boundaries"
hub["data"]["modules"] = [item for item in hub["data"]["modules"] if item["title"] != title]
hub["data"]["modules"].append({
    "title": title,
    "summary": "Reject overflow and narrowing, define decimal rounding, and keep floating-point error visible.",
    "lessons": added,
})
hub["updated_at"] = stamp

reverse = {
    "java/operators": ["java/math-abs-min-value", "java/floor-div-mod-negative", "java/unsigned-integer-parsing"],
    "java/bigdecimal": ["java/bigdecimal-divide-rounding", "java/bigdecimal-setscale-unnecessary", "java/floating-sum-order"],
    "java/checked-integer-arithmetic": ["java/math-abs-min-value", "java/biginteger-exact-conversion", "java/long-to-double-precision"],
    "java/bigdecimal-scale-equality": ["java/bigdecimal-setscale-unnecessary"],
    "java/decimal-parse-boundary": ["java/double-finite-validation"],
    "java/hashset": ["java/double-nan-collection-contracts"],
}
for path, targets in reverse.items():
    entry = lookup[path]
    marker = "<h2>More numeric representation boundaries</h2>"
    entry["body"] = entry["body"].split(marker)[0] + marker + paragraph(
        "Continue with " + ", ".join("[[" + target + "|" + lookup[target]["title"] + "]]" for target in targets) + "."
    )
    entry["updated_at"] = stamp

FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print("Added", len(added), "Java lessons; linked from", len(reverse), "existing lessons")
