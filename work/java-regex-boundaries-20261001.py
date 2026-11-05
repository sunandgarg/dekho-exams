"""Add original Java text-matching boundary lessons to the fixture corpus."""

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
        tags=["java", "regex", slug],
        difficulty="Intermediate",
        sort_order=1200 + len(added),
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
    "regex-quote-user-input",
    "Java Pattern.quote: match a supplied token literally",
    "Pattern.quote turns supplied text into a literal regex operand so punctuation in that text cannot change the match rule.",
    [
        ("Separate the rule from the token", [
            "A routing rule may search for a product code supplied by another system. A code containing a dot is data, not an instruction to match any character. Concatenate the quoted token into the fixed expression; compile the result once when the rule is reused.",
            "The program finds SKU.47 but rejects SKUX47. Without quoting, the dot matches the X as well. [[java/regex-matches-find|matches versus find]] covers the separate question of whether the whole input or a substring must match."
        ]),
        ("Keep a size boundary", [
            "Literal quoting prevents regex syntax injection. It does not cap input length or make an unrelated surrounding expression safe from expensive backtracking. Bound externally supplied tokens before constructing a pattern."
        ]),
    ],
    r'''import java.util.regex.Pattern;

public class ProductTokenSearch {
    public static void main(String[] args) {
        String productCode = "SKU.47";
        Pattern route = Pattern.compile("(?:^|,)" + Pattern.quote(productCode) + "(?:,|$)");
        System.out.println(route.matcher("SKU.47,SKU.48").find());
        System.out.println(route.matcher("SKUX47,SKU.48").find());
    }
}''',
    "true\nfalse",
    "Pattern compilation allocates matcher machinery once; each matcher owns mutable scan state and its cost depends on input size and the surrounding expression. The literal token cannot add regex operators, but an unbounded input still consumes scan time and memory.",
    ["Do not concatenate untrusted text directly into regex syntax.", "Do not share one Matcher across threads; share the compiled Pattern instead.", "Do not treat quoting as an input-length limit."],
    ["java/strings", "java/regex-matches-find", "java/regex-quote-replacement", "java/string-split-trailing-fields"],
)


add(
    "regex-quote-replacement",
    "Java Matcher.quoteReplacement: keep dollar signs and backslashes as data",
    "Matcher replacement strings interpret dollar signs and backslashes, so quoteReplacement is required when a replacement comes from data.",
    [
        ("Two languages meet at replaceAll", [
            "The search expression and replacement string have different parsing rules. Quoting the search token does not quote the replacement. A price label such as $47 can be read as a group reference and fail or produce the wrong text.",
            "This fixture replaces a redacted amount in one ledger note. The first call shows the rejected raw replacement; the second keeps the exact supplied label. [[java/regex-quote-user-input|Pattern.quote]] handles the search side of the same boundary."
        ]),
        ("Do not use regex for a fixed literal replacement", [
            "When both sides are fixed strings and no matching rule is needed, String.replace uses literal character sequences and avoids these regex rules. Use a matcher only when the search criterion actually requires a pattern."
        ]),
    ],
    r'''import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class LedgerLabelReplacement {
    public static void main(String[] args) {
        Matcher amount = Pattern.compile("REDACTED").matcher("settlement=REDACTED");
        String suppliedLabel = "$47\\review";
        try { System.out.println(amount.replaceAll(suppliedLabel)); }
        catch (IndexOutOfBoundsException rejected) { System.out.println("raw replacement rejected"); }
        System.out.println(amount.replaceAll(Matcher.quoteReplacement(suppliedLabel)));
    }
}''',
    "raw replacement rejected\nsettlement=$47\\review",
    "replaceAll constructs a new string; replacement size grows with match count and supplied text length. Quote the replacement at the boundary, then apply an output-size limit if the input may contain many matches.",
    ["Do not assume Pattern.quote affects replacement syntax.", "Do not interpolate a dollar-prefixed label as a group reference.", "Do not use replaceAll when literal String.replace expresses the rule."],
    ["java/regex-quote-user-input", "java/strings", "java/regex-matches-find", "java/stringbuilder"],
)


add(
    "regex-matches-find",
    "Java Matcher.matches and find: whole-input validation versus extraction",
    "Matcher.matches requires the entire input to satisfy a pattern, while find searches for the next matching subsequence.",
    [
        ("Choose validation or search", [
            "An invoice identifier validator must reject a prefixed note, even if a valid-looking identifier appears inside it. A scanner looking for identifiers in log text has the opposite contract. Use matches for the former and find for the latter. Do not paper over this distinction with a leading and trailing wildcard.",
            "A Matcher carries position and last-match state. Build a fresh matcher when changing the task, or call reset deliberately. [[java/regex-find-cursor|Find cursor state]] shows what repeated calls consume."
        ]),
        ("Bound format and input", [
            "The pattern checks a compact ASCII identifier: two uppercase letters, a hyphen and four digits. Real invoice rules may include checksums and length ceilings that a simple regex does not supply. Treat this as a shape check, not proof that an invoice exists."
        ]),
    ],
    r'''import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class InvoiceIdBoundary {
    public static void main(String[] args) {
        Pattern invoiceShape = Pattern.compile("[A-Z]{2}-[0-9]{4}");
        Matcher note = invoiceShape.matcher("paid AB-2741 today");
        System.out.println("valid=" + note.matches());
        System.out.println("found=" + note.find());
        System.out.println("value=" + note.group());
    }
}''',
    "valid=false\nfound=true\nvalue=AB-2741",
    "For this fixed-width pattern, scanning is linear in input length and uses a small matcher state. Other regular expressions can backtrack heavily; validate length before matching and test the actual pattern against hostile inputs.",
    ["Do not use find for a full-field validation rule.", "Do not call group before a successful match.", "Do not reuse a Matcher without accounting for its current scan position."],
    ["java/regex-find-cursor", "java/regex-quote-user-input", "java/strings", "java/regex-group-state"],
)


add(
    "regex-find-cursor",
    "Java Matcher.find: account for the scan cursor and zero-length matches",
    "Each successful Matcher.find advances the matcher search state, including when a pattern can match an empty span.",
    [
        ("Read positions as spans", [
            "An insertion-point pattern can match between characters and at the end. The two numbers from start and end are UTF-16 offsets delimiting a half-open span; they are not byte positions. A zero-width match has equal offsets.",
            "The program prints the positions for an input of two ASCII characters. Java advances its search after an empty match, so the loop terminates. [[java/unicode-encoding|Unicode encoding]] explains why non-ASCII text can make a UTF-16 offset differ from a user-visible character count."
        ]),
        ("Reset for another pass", [
            "Once the search is exhausted, a subsequent find call does not start from the beginning. Call reset or create a fresh matcher when another full pass is required. Do not hand-roll an extra cursor increment on the same matcher without testing endpoint behavior."
        ]),
    ],
    r'''import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class InsertionPointScanner {
    public static void main(String[] args) {
        Matcher boundaries = Pattern.compile("(?=.)|$").matcher("AB");
        while (boundaries.find()) {
            System.out.println(boundaries.start() + ":" + boundaries.end());
        }
    }
}''',
    "0:0\n1:1\n2:2",
    "This fixture visits three positions with constant matcher storage. In general, cost depends on the pattern and input; zero-width matches can multiply output records, so cap emitted matches for untrusted text.",
    ["Do not treat start and end as byte offsets.", "Do not call group before a successful find.", "Do not assume an empty match leaves find stuck forever."],
    ["java/regex-matches-find", "java/regex-group-state", "java/unicode-encoding", "java/strings"],
)


add(
    "regex-group-state",
    "Java Matcher groups: distinguish absent optional captures from empty text",
    "A Matcher group is available only after a successful match; an unmatched optional group returns null, while a matched empty group returns an empty string.",
    [
        ("Keep three states separate", [
            "A parser may allow an optional region code after a ticket number. No region, an explicitly empty region, and a nonempty region can mean different things at an API boundary. The capture result must preserve that distinction until validation decides whether an empty region is legal.",
            "Named groups improve reviewability when a pattern has several fields. The program checks both cases by constructing new matchers, then prints whether the optional group is absent or present. [[java/regex-matches-find|Match scope]] explains the preceding whole-input check."
        ]),
        ("Validate before reading", [
            "Calling group on a matcher without a successful matches or find call throws IllegalStateException. A parser should reject the input before it asks for fields, then convert captured text to typed values with range checks."
        ]),
    ],
    r'''import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class TicketRegionCapture {
    public static void main(String[] args) {
        Pattern ticketShape = Pattern.compile("(?<ticket>T-[0-9]{3})(?:\\[(?<region>[A-Z]*)\\])?");
        for (String ticketText : new String[] {"T-247", "T-247[]", "T-247[EU]"}) {
            Matcher parsed = ticketShape.matcher(ticketText);
            if (!parsed.matches()) throw new IllegalArgumentException(ticketText);
            String region = parsed.group("region");
            System.out.println(region == null ? "absent" : "region='" + region + "'");
        }
    }
}''',
    "absent\nregion=''\nregion='EU'",
    "The fixed-width ticket field bounds work here. Each Matcher stores match state; the captured strings allocate from the input. For large or adversarial fields, cap length before matching and reject optional empty fields if the domain forbids them.",
    ["Do not collapse null and empty captures into one value without a policy.", "Do not read group before a successful match.", "Do not use a regex shape check as a substitute for identifier lookup."],
    ["java/regex-matches-find", "java/regex-find-cursor", "java/regex-unicode-flags", "java/strings"],
)


add(
    "regex-unicode-flags",
    "Java regex Unicode classes: decide what a word character means",
    "Java regex predefined word classes use an ASCII-oriented default in Java 8; UNICODE_CHARACTER_CLASS changes the predefined class behavior for Unicode text.",
    [
        ("Declare the character policy", [
            "A customer identifier containing an accented letter is not accepted by an ASCII-only word rule. The same regex source can accept it when compiled with UNICODE_CHARACTER_CLASS. Neither setting is universally correct: protocol identifiers may require ASCII, while human names need a more deliberate policy than word characters alone.",
            "The fixture compares one identifier under both flags. [[java/text-normalization|Text normalization]] handles canonically equivalent spellings; changing regex flags does not normalize the input. [[java/unicode-encoding|Unicode representation]] covers code points and encoded bytes."
        ]),
        ("Avoid vague name validation", [
            "Names contain spaces, punctuation, scripts and conventions that a word-character rule misses. Keep the example as an identifier policy. If stored identifiers must compare consistently, define normalization and case rules separately before persistence."
        ]),
    ],
    r'''import java.util.regex.Pattern;

public class CustomerCodeCharacterPolicy {
    public static void main(String[] args) {
        String customerCode = "Café_47";
        Pattern ascii = Pattern.compile("\\w+");
        Pattern unicode = Pattern.compile("\\w+", Pattern.UNICODE_CHARACTER_CLASS);
        System.out.println("ascii=" + ascii.matcher(customerCode).matches());
        System.out.println("unicode=" + unicode.matcher(customerCode).matches());
    }
}''',
    "ascii=false\nunicode=true",
    "Both patterns scan this short input with small state. More permissive character classes can admit values that downstream systems reject; validate the full storage and protocol contract rather than assuming a Unicode flag settles it.",
    ["Do not assume the default word class covers every letter.", "Do not treat a Unicode class flag as text normalization.", "Do not use a generic word rule as a complete human-name validator."],
    ["java/text-normalization", "java/unicode-encoding", "java/regex-matches-find", "java/strings"],
)


add(
    "regex-split-limit",
    "Java String.split limit: retain trailing empty fields in records",
    "String.split(regex, -1) preserves trailing empty fields that the default split call discards.",
    [
        ("Preserve the record width", [
            "A delimited import line may end with an empty optional note. If a parser discards that final field, a schema-width check can accept or reject the wrong record. A negative split limit keeps the final empty string; a positive limit can instead cap the number of pieces when the final field may contain delimiters.",
            "The delimiter is a regex. A literal pipe must be quoted or escaped; [[java/regex-quote-user-input|quoting user text]] covers a delimiter supplied at runtime. The existing [[java/string-split-trailing-fields|trailing-fields lesson]] introduces this issue; this page adds an explicit schema-width gate and a bounded split contract."
        ]),
        ("Limit allocations", [
            "Splitting an entire untrusted line creates an array and substrings. Cap line length and expected field count first. If a field can contain escaped delimiters or quoted text, a plain split call is the wrong parser."
        ]),
    ],
    r'''import java.util.Arrays;
import java.util.regex.Pattern;

public class ManifestFieldWidth {
    public static void main(String[] args) {
        String manifestLine = "R-47|ready|";
        String separator = Pattern.quote("|");
        String[] defaultFields = manifestLine.split(separator);
        String[] preservedFields = manifestLine.split(separator, -1);
        System.out.println("default=" + defaultFields.length);
        System.out.println("preserved=" + Arrays.toString(preservedFields));
        String[] bounded = "R-47|ready|note|with|pipes".split(separator, 3);
        System.out.println("bounded=" + Arrays.toString(bounded));
    }
}''',
    "default=2\npreserved=[R-47, ready, ]\nbounded=[R-47, ready, note|with|pipes]",
    "Split scans the input and allocates an array plus result strings. A positive limit bounds the number of pieces, not the input length or final piece size. Validate both record length and schema before storing the fields.",
    ["Do not use the default split call when trailing blanks are meaningful.", "Do not assume the separator argument is literal text.", "Do not use split to parse a quoted CSV-style format."],
    ["java/string-split-trailing-fields", "java/regex-quote-user-input", "java/bounded-line-reader", "java/strings"],
)


for path in added:
    entry = lookup[path]
    entry["data"]["related"] = [
        {"path": target, "title": lookup[target]["title"]}
        for target in entry.pop("_related_paths")
    ]

hub = lookup["java/java"]
title = "Text matching boundaries"
hub["data"]["modules"] = [module for module in hub["data"]["modules"] if module["title"] != title]
hub["data"]["modules"].append({
    "title": title,
    "summary": "Keep supplied tokens literal, retain parser fields, and distinguish full validation from searching.",
    "lessons": added,
})
hub["updated_at"] = stamp

reverse = {
    "java/strings": ["java/regex-quote-user-input", "java/regex-matches-find", "java/regex-split-limit"],
    "java/string-split-trailing-fields": ["java/regex-split-limit", "java/regex-quote-user-input"],
    "java/text-normalization": ["java/regex-unicode-flags"],
    "java/unicode-encoding": ["java/regex-unicode-flags", "java/regex-find-cursor"],
}
for path, targets in reverse.items():
    entry = lookup[path]
    marker = "<h2>Text matching boundaries</h2>"
    entry["body"] = entry["body"].split(marker)[0] + marker + paragraph(
        "Continue with " + ", ".join("[[" + target + "|" + lookup[target]["title"] + "]]" for target in targets) + "."
    )
    entry["updated_at"] = stamp

FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print("Added", len(added), "Java lessons; linked from", len(reverse), "existing lessons")
