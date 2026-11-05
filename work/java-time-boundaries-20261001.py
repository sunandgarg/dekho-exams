"""Add original Java time boundary lessons with executable examples."""

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
        tags=["java", "time", slug],
        difficulty="Intermediate",
        sort_order=1060 + len(added),
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
    "duration-versus-period-dst",
    "Java Duration versus Period across a daylight-saving change",
    "Duration measures elapsed seconds, while Period advances calendar fields on a date or zoned date-time.",
    [
        ("Choose a timeline", [
            "A shipping deadline 24 hours from now needs Duration. A daily collection at noon needs calendar-day arithmetic. In Europe/Paris, the spring clock change makes those two rules produce different wall times even though both are described casually as one day later.",
            "The fixture starts before the 2024 spring transition. Calendar addition keeps noon and spans 23 elapsed hours; a 24-hour duration lands at 13:00. [[java/zone-transitions|Gap and overlap rules]] explain why a local date-time cannot always be converted to one instant without policy."
        ]),
        ("Persist the right value", [
            "An absolute expiry belongs on the instant timeline. A recurring local appointment needs its local rule and region zone, not merely the next computed instant. [[java/clock-injection|Injected clocks]] make expiry tests deterministic."
        ]),
    ],
    '''import java.time.Duration;
import java.time.Period;
import java.time.ZoneId;
import java.time.ZonedDateTime;

public class ParisCollectionSchedule {
    public static void main(String[] args) {
        ZonedDateTime pickup = ZonedDateTime.of(2024, 3, 30, 12, 0, 0, 0, ZoneId.of("Europe/Paris"));
        ZonedDateTime calendarNext = pickup.plus(Period.ofDays(1));
        ZonedDateTime elapsedNext = pickup.plus(Duration.ofDays(1));
        System.out.println(calendarNext.toLocalTime());
        System.out.println(elapsedNext.toLocalTime());
        System.out.println(Duration.between(pickup, calendarNext).toHours());
    }
}''',
    "12:00\n13:00\n23",
    "Both operations use fixed-size time objects and constant application storage. Their computational cost is small relative to persistence or scheduling, but their business meanings differ by an hour here; converting a recurring rule into a duration loses that rule.",
    ["Do not substitute 24 hours for a calendar day in a regional schedule.", "Do not store only the next instant for a recurring local-time rule.", "Do not compare LocalDateTime values as if they were elapsed timestamps."],
    ["java/zone-transitions", "java/date-time", "java/clock-injection", "java/zoned-zone-conversion"],
)


add(
    "zoned-zone-conversion",
    "Java ZonedDateTime zone conversion: preserve the instant or the wall clock",
    "withZoneSameInstant preserves a point on the timeline; withZoneSameLocal preserves displayed local fields and may change the instant.",
    [
        ("State what a transfer means", [
            "A meeting transferred to another region usually keeps its instant. A store schedule copied to a new branch may keep its local opening time instead. Calling a zone conversion without naming that choice silently changes the business rule.",
            "The fixture moves a Delhi dispatch to Paris on a fixed date. The same-instant conversion changes the wall clock; the same-local conversion keeps 09:30 and moves the underlying instant. [[java/offsetdatetime-same-instant|OffsetDateTime comparisons]] show why equal instants need not have equal representations."
        ]),
        ("Handle invalid local times", [
            "A same-local conversion can land in a gap or overlap in the target region. It applies zone-resolution rules; if a booking must never shift, validate the target local fields first with [[java/zone-transitions|valid offsets]] and reject ambiguity according to the product contract."
        ]),
    ],
    '''import java.time.ZoneId;
import java.time.ZonedDateTime;

public class DispatchZoneTransfer {
    public static void main(String[] args) {
        ZonedDateTime delhi = ZonedDateTime.of(2024, 1, 15, 9, 30, 0, 0, ZoneId.of("Asia/Kolkata"));
        ZoneId paris = ZoneId.of("Europe/Paris");
        ZonedDateTime sameInstant = delhi.withZoneSameInstant(paris);
        ZonedDateTime sameLocal = delhi.withZoneSameLocal(paris);
        System.out.println(sameInstant.toLocalTime());
        System.out.println(sameLocal.toLocalTime());
        System.out.println(delhi.toInstant().equals(sameInstant.toInstant()));
        System.out.println(delhi.toInstant().equals(sameLocal.toInstant()));
    }
}''',
    "05:00\n09:30\ntrue\nfalse",
    "Each conversion creates an immutable value with constant application storage. Rule lookup depends on the zone database. A region's future rules may change, so persist the region and scheduling intent when future local time is the requirement.",
    ["Do not use withZoneSameLocal for a completed event timestamp.", "Do not assume the same wall clock means the same instant.", "Do not silently accept a target-region gap for an exact appointment."],
    ["java/date-time", "java/zone-transitions", "java/offsetdatetime-same-instant", "java/duration-versus-period-dst"],
)


add(
    "offsetdatetime-same-instant",
    "Java OffsetDateTime equality versus isEqual for event timestamps",
    "OffsetDateTime.equals compares local fields and offset, while isEqual tests whether two values identify the same instant.",
    [
        ("Pick an identity rule", [
            "Two services can serialize the same event using different offsets. A Set keyed by OffsetDateTime uses equals and can retain both representations. If deduplication is about the event's position on the timeline, normalize to Instant or compare with isEqual. Do not redefine that rule accidentally through formatting.",
            "The two values below are one event seen at UTC and at +05:30. Their printed local clocks differ. [[java/zoned-zone-conversion|Zone conversion]] has the same representation-versus-instant distinction for region-based values."
        ]),
        ("Preserve context when required", [
            "An Instant is enough for ordering a completed event, but it does not tell you the customer's original offset or region. Store those separately when audit or display policy requires them. [[java/date-time|Time-type selection]] starts from the question the application needs to answer."
        ]),
    ],
    '''import java.time.OffsetDateTime;

public class ReceiptTimestampIdentity {
    public static void main(String[] args) {
        OffsetDateTime utc = OffsetDateTime.parse("2024-08-12T04:00:00Z");
        OffsetDateTime delhiOffset = OffsetDateTime.parse("2024-08-12T09:30:00+05:30");
        System.out.println(utc.equals(delhiOffset));
        System.out.println(utc.isEqual(delhiOffset));
        System.out.println(utc.toInstant().equals(delhiOffset.toInstant()));
    }
}''',
    "false\ntrue\ntrue",
    "The comparison uses fixed-size immutable values. The important cost is logical: a collection keyed by representation can double-count one event. Normalize once at the identity boundary rather than repeatedly converting every time the set is read.",
    ["Do not use equals as an instant-equivalence test for OffsetDateTime.", "Do not discard original offset context if an audit requires it.", "Do not confuse a numeric offset with a region's future zone rules."],
    ["java/zoned-zone-conversion", "java/date-time", "java/instant-epoch-millis-truncation", "java/zone-transitions"],
)


add(
    "yearmonth-end-of-month",
    "Java YearMonth.atEndOfMonth: calculate a month boundary without guessed days",
    "YearMonth.atEndOfMonth returns the actual final LocalDate of a month, including leap-year February.",
    [
        ("Compute the boundary from the calendar", [
            "A billing period ending in February does not have a constant day count. YearMonth carries the year and month without inventing a day; atEndOfMonth resolves the final date. The fixture prints February in a leap year and a non-leap year.",
            "For a half-open timestamp range, use the first day of the next month as the exclusive end, then resolve that local boundary in the customer's zone. [[java/localdate-exclusive-range|Exclusive date ranges]] avoid a fabricated last instant with guessed precision."
        ]),
        ("Keep policy separate from representation", [
            "A calendar month is not thirty elapsed days. If a contract renews on the last day, recompute from YearMonth each cycle. [[java/period-month-end-arithmetic|Repeated plusMonths]] can drift after a short month."
        ]),
    ],
    '''import java.time.YearMonth;

public class InvoiceMonthBoundary {
    public static void main(String[] args) {
        System.out.println(YearMonth.of(2024, 2).atEndOfMonth());
        System.out.println(YearMonth.of(2025, 2).atEndOfMonth());
        System.out.println(YearMonth.of(2024, 2).plusMonths(1).atDay(1));
    }
}''',
    "2024-02-29\n2025-02-28\n2024-03-01",
    "YearMonth and LocalDate are immutable fixed-size values. The operation is constant application work and storage; the larger risk is using a guessed day count and billing a different range from the one stated to users.",
    ["Do not hard-code February 28 as its last day.", "Do not model a calendar month as a fixed Duration.", "Do not append 23:59:59 as a substitute for an exclusive upper bound."],
    ["java/localdate-exclusive-range", "java/period-month-end-arithmetic", "java/duration-versus-period-dst", "java/date-time"],
)


add(
    "formatter-week-year-boundary",
    "Java DateTimeFormatter week-year Y versus calendar year u",
    "DateTimeFormatter pattern Y prints the week-based year, which can differ from the calendar year printed by u.",
    [
        ("Keep identifiers out of the wrong calendar", [
            "A date near New Year can belong to the first ISO week of the following week-based year. If an invoice ID uses YYYY-MM-dd by mistake, its year can disagree with its month and day. Use uuuu-MM-dd for a calendar date, or explicitly format a week date when that is the intended business identifier.",
            "The fixture fixes Locale.UK so week conventions do not depend on the machine default. December 30, 2019 has calendar year 2019 but belongs to week 1 of week-based year 2020. [[java/strict-date-parsing|Strict input parsing]] covers validation after choosing the correct fields."
        ]),
        ("Make locale part of the contract", [
            "Week numbering varies by locale. A persisted week identifier needs a declared convention; changing the JVM default locale must not change existing keys. Prefer explicit WeekFields or a fixed formatter locale, and test year boundaries."
        ]),
    ],
    '''import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.Locale;

public class ShipmentWeekIdentifier {
    public static void main(String[] args) {
        LocalDate shipped = LocalDate.of(2019, 12, 30);
        DateTimeFormatter calendar = DateTimeFormatter.ofPattern("uuuu-MM-dd", Locale.UK);
        DateTimeFormatter week = DateTimeFormatter.ofPattern("YYYY-'W'ww-e", Locale.UK);
        System.out.println(shipped.format(calendar));
        System.out.println(shipped.format(week));
    }
}''',
    "2019-12-30\n2020-W01-1",
    "Formatting a fixed date uses bounded application storage and work. Persisted identifiers carry a larger migration cost if the wrong year field was used; changing the formatter later does not repair keys already issued.",
    ["Do not use YYYY for a calendar-year date field.", "Do not rely on the process default locale for persisted week keys.", "Do not change an existing week convention without a migration plan."],
    ["java/strict-date-parsing", "java/date-time", "java/yearmonth-end-of-month", "java/resource-bundles"],
)


add(
    "instant-epoch-millis-truncation",
    "Java Instant toEpochMilli: detect lost submillisecond precision",
    "Instant.toEpochMilli converts a timestamp to whole milliseconds, dropping its finer nanosecond fraction.",
    [
        ("Declare storage precision", [
            "An Instant can represent nanosecond fields, but a database column or wire field holding epoch milliseconds cannot. Converting and rebuilding the value loses the last six digits of the nanosecond field. That is a schema choice, not a harmless serialization detail.",
            "The fixture shows an event with 123456789 nanoseconds becoming 123000000 after a millisecond round trip. [[java/offsetdatetime-same-instant|Offset representations]] are a separate concern: equal instants can be written with different offsets even without precision loss."
        ]),
        ("Bound comparisons to stored precision", [
            "If the store truncates to milliseconds, compare against an Instant truncated to that unit or use an agreed tolerance. Never silently assume that a round trip preserves equality. For ordering events with the same stored millisecond, add a separate sequence or stable tie-break key."
        ]),
    ],
    '''import java.time.Instant;

public class LedgerTimestampPrecision {
    public static void main(String[] args) {
        Instant captured = Instant.parse("2024-08-12T04:00:00.123456789Z");
        Instant stored = Instant.ofEpochMilli(captured.toEpochMilli());
        System.out.println(captured.getNano());
        System.out.println(stored.getNano());
        System.out.println(captured.equals(stored));
    }
}''',
    "123456789\n123000000\nfalse",
    "The conversion is constant application work and storage. Precision loss is irreversible after persistence; if a service needs finer ordering, choose a matching schema and serialization format before writing data.",
    ["Do not expect toEpochMilli to preserve nanoseconds.", "Do not use timestamp equality across storage systems with different precision without a policy.", "Do not infer event order solely from a coarse timestamp when collisions are possible."],
    ["java/offsetdatetime-same-instant", "java/date-time", "java/clock-injection", "java/checked-integer-arithmetic"],
)


add(
    "localdate-exclusive-range",
    "Java LocalDate half-open ranges: define an exclusive end",
    "A half-open date range includes its start and excludes its end, so adjacent ranges meet without overlap.",
    [
        ("Use one boundary convention", [
            "A monthly report can represent February as [February 1, March 1). The next report starts exactly where the first ends. No last-second adjustment is needed, and leap years are handled by calendar arithmetic rather than manual day counts.",
            "The fixture checks the final day of February and the next day's exclusion. [[java/yearmonth-end-of-month|YearMonth]] can supply the start of the next month; a timestamp query must convert each local boundary using an explicit zone and its transition policy."
        ]),
        ("Keep date ranges and instant ranges distinct", [
            "A LocalDate range answers which civil dates belong to a report. An Instant range answers which events fall on a timeline. The conversion between them requires the user's zone and may span 23 or 25 hours around daylight-saving changes; [[java/duration-versus-period-dst|calendar versus elapsed time]] explains that difference."
        ]),
    ],
    '''import java.time.LocalDate;
import java.time.YearMonth;

public class InvoiceDateWindow {
    static boolean includes(LocalDate candidate, LocalDate start, LocalDate endExclusive) {
        if (!start.isBefore(endExclusive)) throw new IllegalArgumentException("empty window");
        return !candidate.isBefore(start) && candidate.isBefore(endExclusive);
    }

    public static void main(String[] args) {
        YearMonth period = YearMonth.of(2024, 2);
        LocalDate start = period.atDay(1);
        LocalDate endExclusive = period.plusMonths(1).atDay(1);
        System.out.println(includes(LocalDate.of(2024, 2, 29), start, endExclusive));
        System.out.println(includes(LocalDate.of(2024, 3, 1), start, endExclusive));
    }
}''',
    "true\nfalse",
    "Each membership test is constant work and storage. A database query should use the same inclusive lower and exclusive upper bound. If its columns are timestamps, resolve the local dates to instants before querying rather than comparing formatted strings.",
    ["Do not use an inclusive 23:59:59 upper timestamp; it misses finer precision.", "Do not combine local dates with UTC timestamps without a zone rule.", "Do not accept reversed or empty bounds silently."],
    ["java/yearmonth-end-of-month", "java/duration-versus-period-dst", "java/date-time", "java/zone-transitions"],
)


add(
    "offset-validated-against-zone",
    "Java ZoneRules: validate a saved offset against a local booking",
    "A local date-time and region zone can have zero, one, or two valid offsets, so a saved offset must be checked against that zone's rules.",
    [
        ("Reject mismatched booking data", [
            "An offset sent with a booking is useful during an autumn overlap, when the same local time occurs twice. It is not arbitrary. Check that the offset is among the region's valid offsets before creating the scheduled instant. A stale or forged offset can point to a different instant from the one implied by the region.",
            "The fixture uses a Paris overlap with two accepted offsets and rejects +03:00. [[java/zone-transitions|Gap and overlap detection]] introduces the transition rules; this lesson applies them to persisted input validation."
        ]),
        ("Separate validation from future rule changes", [
            "A future booking may be affected by time-zone database updates. Store the local intention, region, and chosen overlap policy. A saved instant is useful for current execution, but a long-lived recurring schedule may need recomputation when rules change."
        ]),
    ],
    '''import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.time.zone.ZoneRules;

public class BookingOffsetGate {
    static boolean accepted(LocalDateTime local, ZoneId region, ZoneOffset supplied) {
        ZoneRules rules = region.getRules();
        return rules.getValidOffsets(local).contains(supplied);
    }

    public static void main(String[] args) {
        LocalDateTime booking = LocalDateTime.of(2024, 10, 27, 2, 30);
        ZoneId paris = ZoneId.of("Europe/Paris");
        System.out.println(accepted(booking, paris, ZoneOffset.ofHours(2)));
        System.out.println(accepted(booking, paris, ZoneOffset.ofHours(1)));
        System.out.println(accepted(booking, paris, ZoneOffset.ofHours(3)));
    }
}''',
    "true\ntrue\nfalse",
    "Validation uses a small list of valid offsets and constant application storage. Zone-rule lookup is cheap for a single booking, but the rule database is versioned; policy and stored values must be reviewed when scheduling far into the future.",
    ["Do not accept any syntactically valid offset for a region booking.", "Do not assume an overlap has only one valid instant.", "Do not store a bare LocalDateTime as the full identity of an overlapped booking."],
    ["java/zone-transitions", "java/zoned-zone-conversion", "java/date-time", "java/strict-date-parsing"],
)


add(
    "duration-negative-components",
    "Java negative Duration fields: seconds and nanos are normalized",
    "A negative Duration stores a signed seconds field and a nonnegative nanosecond adjustment, so its components can surprise callers.",
    [
        ("Compare the whole duration", [
            "A duration of negative 1.5 seconds is represented as seconds -2 plus 500 million nanos. Printing getSeconds and getNano separately can look contradictory if the reader assumes both components share a sign. Use toMillis, compareTo, or the whole value when making a deadline decision.",
            "The fixture prints the components and the total milliseconds. [[java/clock-injection|Expiry checks]] should compare Instants directly when the business rule is before or after a deadline."
        ]),
        ("Keep unit conversion explicit", [
            "Conversions to whole units can discard a fractional remainder. A negative duration close to zero needs careful treatment if a UI displays rounded seconds or an API accepts integer milliseconds. Do not make a retry decision from a rounded display value."
        ]),
    ],
    '''import java.time.Duration;

public class RetryDelayDebt {
    public static void main(String[] args) {
        Duration overdue = Duration.ofMillis(-1500);
        System.out.println(overdue.getSeconds());
        System.out.println(overdue.getNano());
        System.out.println(overdue.toMillis());
        System.out.println(overdue.isNegative());
    }
}''',
    "-2\n500000000\n-1500\ntrue",
    "Duration is a fixed-size immutable value, and these conversions use constant application work. The failure risk is interpreting one component as the signed total or truncating a fractional duration before a boundary comparison.",
    ["Do not infer the total sign from getNano.", "Do not rebuild a negative duration by giving both fields the same sign.", "Do not round a deadline interval before deciding whether work is overdue."],
    ["java/duration-versus-period-dst", "java/clock-injection", "java/date-time", "java/instant-epoch-millis-truncation"],
)


add(
    "period-month-end-arithmetic",
    "Java plusMonths at month end: prevent renewal-date drift",
    "Adding one month to a date near month end can clamp the day, so repeated additions may differ from an addition anchored to the original date.",
    [
        ("Keep the original recurrence rule", [
            "A contract signed on January 31 may intend the last day of every month. Repeatedly adding one month to the previous invoice date loses that intent after February clamps the day. Calculate each occurrence from the anchor month and a declared day policy instead.",
            "The fixture shows January 31, 2024 plus one month becomes February 29; another plus one month becomes March 29. Directly adding two months to January 31 yields March 31. [[java/yearmonth-end-of-month|YearMonth.atEndOfMonth]] expresses an explicit last-day policy."
        ]),
        ("Make the policy testable", [
            "Some products want the 31st where it exists and the last day otherwise; others want the 29th after the first clamp. Either can be valid. The error is allowing the library's chained arithmetic to choose the policy without review."
        ]),
    ],
    '''import java.time.LocalDate;
import java.time.YearMonth;

public class ContractRenewalAnchor {
    public static void main(String[] args) {
        LocalDate signed = LocalDate.of(2024, 1, 31);
        LocalDate chained = signed.plusMonths(1).plusMonths(1);
        LocalDate anchored = signed.plusMonths(2);
        LocalDate lastDayPolicy = YearMonth.from(signed).plusMonths(2).atEndOfMonth();
        System.out.println(signed.plusMonths(1));
        System.out.println(chained);
        System.out.println(anchored);
        System.out.println(lastDayPolicy);
    }
}''',
    "2024-02-29\n2024-03-29\n2024-03-31\n2024-03-31",
    "Each calculation uses fixed-size immutable dates. A billing scheduler should retain its anchor and recurrence rule rather than derive future dates solely from the last emitted date; otherwise a one-time clamp can permanently alter the sequence.",
    ["Do not assume repeated plusMonths preserves the original day of month.", "Do not encode a last-day rule as an accidental side effect of clamping.", "Do not model a renewal month as a fixed number of elapsed hours."],
    ["java/yearmonth-end-of-month", "java/localdate-exclusive-range", "java/duration-versus-period-dst", "java/date-time"],
)


for path in added:
    entry = lookup[path]
    entry["data"]["related"] = [
        {"path": target, "title": lookup[target]["title"]}
        for target in entry.pop("_related_paths")
    ]

hub = lookup["java/advanced-java"]
title = "Calendar and timestamp contracts"
hub["data"]["modules"] = [item for item in hub["data"]["modules"] if item["title"] != title]
hub["data"]["modules"].append({
    "title": title,
    "summary": "Separate elapsed time, civil schedules, precision, and zone-offset validation.",
    "lessons": added,
})
hub["updated_at"] = stamp

reverse = {
    "java/date-time": ["java/duration-versus-period-dst", "java/zoned-zone-conversion", "java/offsetdatetime-same-instant", "java/yearmonth-end-of-month"],
    "java/zone-transitions": ["java/duration-versus-period-dst", "java/offset-validated-against-zone", "java/zoned-zone-conversion"],
    "java/strict-date-parsing": ["java/formatter-week-year-boundary", "java/offset-validated-against-zone"],
    "java/clock-injection": ["java/instant-epoch-millis-truncation", "java/duration-negative-components"],
}
for path, targets in reverse.items():
    entry = lookup[path]
    marker = "<h2>More calendar and timestamp contracts</h2>"
    entry["body"] = entry["body"].split(marker)[0] + marker + paragraph(
        "Continue with " + ", ".join("[[" + target + "|" + lookup[target]["title"] + "]]" for target in targets) + "."
    )
    entry["updated_at"] = stamp

FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print("Added", len(added), "Java lessons; linked from", len(reverse), "existing lessons")
