"""Add distinct CSS decisions for fonts, numbering, assets, and color output."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path


root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
hub_path = "css/css-tutorial/reference"
quiz_path = "quizzes/css-type-color-assets"
specs = []


def add(slug, title, summary, definition, decision, sample, cost, mistakes, related):
    path = "css/" + slug
    assert path not in by_path
    specs.append(dict(path=path, title=title, summary=summary, definition=definition,
                      decision=decision, sample=sample, cost=cost, mistakes=mistakes,
                      related=related))


add("variable-font-weight-range", "CSS variable fonts: declare the supported weight range",
    "Expose a variable font's real weights before asking for intermediate values.",
    "A variable font can contain a continuous weight axis within a declared range. The @font-face font-weight descriptor tells the browser which weights the file can supply; an ordinary font-weight declaration then requests a value from that range.",
    "A reconciliation dashboard uses one family for headings and dense numerical labels. Its selected variable font file has a documented weight range from 320 to 720, and the card heading requests 620 to separate it from body text without loading another static file. Declare the actual range, not an imagined one. The sample names a deployment asset that must exist before the rule is shipped; system-ui remains the font fallback. Inspect the rendered font in developer tools, because a misspelled family or failed request can make a fallback font appear to prove the weight works. Compare regular and heading weights at small sizes, high zoom, and with a long translated title. If the font file lacks the requested range, the browser may choose or synthesize a different face. Use font-weight for the registered weight axis; reserve font-variation-settings for axes without a suitable higher-level property.",
    "@font-face { font-family: 'Ledger Variable'; src: url('/assets/ledger-variable.woff2') format('woff2'); font-style: normal; font-weight: 320 720; font-display: swap; }\n.ledger-card { font-family: 'Ledger Variable', system-ui, sans-serif; }\n.ledger-card__title { font-weight: 620; }",
    "A single variable file can replace several weight files, but its transfer size is not automatically smaller. Inspect the real WOFF2 size and the font-loading waterfall before choosing it. A swap can change line breaks if fallback metrics differ, so test the title before and after font load. The file path in this lesson is illustrative; a missing file leaves the fallback family, which may have different metrics and no intermediate weight. Keep the range accurate to the actual font metadata. Serving a full multilingual variable font when a small subset suffices can cost more bytes than a few static faces. The content remains text and should stay readable while fonts load.",
    ["Do not declare a weight range the file does not contain.", "Do not treat a fallback font as proof that the variable file loaded.", "Do not use low-level axis settings for an ordinary font-weight decision."],
    ["css/font-loading", "css/font-shorthand-stack", "css/font-size-adjust-fallback"])

add("font-optical-sizing-check", "CSS font-optical-sizing: inspect the font's size-specific drawings",
    "Let an optical-size axis follow text size when the selected face supports it.",
    "Font optical sizing lets a font with an opsz axis adjust its glyph drawings for the rendered size. The auto value is the normal behavior for a supporting font; none disables this automatic adjustment. A font without the axis will not gain one from CSS.",
    "The same report family appears in a small footnote and a large case title. If the actual variable font contains an optical-size axis, leaving auto in place can produce drawings intended for each size. Explicitly declaring auto in the sample records the design decision, but it is not a substitute for checking the file. Compare the exact title and footnote at their production sizes and inspect strokes, counters, and line breaks on target devices. Do not lock a numeric opsz value for all sizes merely because a large heading looks attractive in a screenshot. A fallback font may respond differently or not at all. Keep the ordinary font-size and line-height rules responsible for readability; optical sizing changes glyph design, not semantic hierarchy, content, or zoom behavior. Test a print export too if the report is distributed as a document.",
    ".case-report { font-family: 'Ledger Variable', system-ui, sans-serif; font-optical-sizing: auto; }\n.case-report__title { font-size: 2.15rem; line-height: 1.15; }\n.case-report__footnote { font-size: .82rem; line-height: 1.45; }",
    "The declaration itself adds little runtime work, while the font file and its fallback metrics dominate delivery and layout changes. A variable file with an opsz axis may be larger than a static alternative; measure the delivered subset. Optical sizing can alter glyph width enough to change wrapping, so verify the longest title and the smallest annotation after the real font loads. If the axis is absent, the rule is effectively inert. Avoid making the comparison with a substituted local font whose family name happens to match. Screen and print rasterization differ; judge legibility in the contexts that matter instead of assuming one screenshot settles it.",
    ["Do not assume every variable font has an opsz axis.", "Do not hard-code one optical size for both footnotes and titles.", "Do not confuse optical sizing with font-size or line-height."],
    ["css/variable-font-weight-range", "css/readable-type", "css/font-loading"])

add("font-synthesis-boundary", "CSS font-synthesis-weight: prevent a counterfeit bold face",
    "Disable synthesized weight only after supplying a real readable emphasis face.",
    "When a family lacks a requested bold weight, a browser may synthesize a heavier appearance. Font-synthesis-weight controls whether that synthesized weight is permitted. Setting none does not create a missing bold file or guarantee that emphasized text remains visually distinct.",
    "A legal notice uses a supplied regular and semibold family, so a mechanically thickened face would distort the approved letterforms. Scope the no-synthesis rule to the notice and request the actual available semibold weight for its emphasis. Test the regular face, the loaded semibold face, and the system fallback when the font request fails. If the fallback has no suitable semibold, the browser may choose a nearby real weight or show much weaker emphasis once synthesis is disabled; the notice must still communicate emphasis through its words and structure. Do not apply the rule across the entire site before auditing every font family and language subset. CJK or accented glyphs may come from a different face than the Latin title, so inspect mixed-script text. A typographic policy cannot replace semantic strong emphasis in the document.",
    ".legal-notice { font-family: 'Ledger Variable', system-ui, sans-serif; font-synthesis-weight: none; }\n.legal-notice strong { font-weight: 620; }",
    "Preventing synthesized bold can preserve a typeface's design, but it can also remove the visible weight difference when the intended face is missing. That is a correctness and accessibility risk, not a performance optimization. Check real font downloads and fallback rendering under network failure. If separate language subsets load at different times, visible weights may change as glyph fallback resolves. Keep the rule local and pair it with a known available font-weight range. Disabling synthesis does not shrink the font payload; it may require shipping a heavier face or a variable font that covers the desired weight. Test at normal and high zoom rather than judging only large headings.",
    ["Do not disable synthetic weight without supplying a real emphasis weight.", "Do not assume every script in the notice comes from the same file.", "Do not replace semantic strong text with a visual weight alone."],
    ["css/variable-font-weight-range", "css/font-loading", "html/inline-text-meaning"])

add("counter-style-fallback", "CSS @counter-style: give a finite marker set an honest fallback",
    "Use custom ordered-list markers for a short process while preserving numbering beyond the designed set.",
    "The @counter-style rule defines a marker system for lists and generated counters. A fixed system supplies a finite sequence of symbols; its fallback descriptor defines how values outside that sequence appear. The ordered list still carries the sequence in HTML.",
    "An incident review has three named stages today, represented by distinct circled markers. The process may gain a fourth stage later, so the marker definition falls back to decimal rather than repeating the first symbol or displaying an empty marker. Declare decimal before the custom style on the list so an unsupported browser keeps ordinary numbering. Test four and five stages, a list beginning at a nondefault value, browser zoom, and fonts that lack the circled glyphs. The style should never be the only way a reader learns a stage name; keep each item label in actual text. Numbered steps require an ol element in the document, not three visually numbered div elements. If the markers are essential to compliance documentation, review assistive-technology output because custom glyphs are announced differently across combinations of browsers and readers.",
    "@counter-style review-stage { system: fixed; symbols: '①' '②' '③'; suffix: ' '; fallback: decimal; }\n.review-steps { list-style-type: decimal; list-style-type: review-stage; padding-inline-start: 2.25rem; }",
    "The marker rule is cheap to render. The more material cost is font coverage and consistency across print and assistive technology. A missing glyph may become a replacement character or a visually different symbol, so compare target platforms. A fixed system with fallback is safer than a cyclic one when repetition would falsely imply that stage four is stage one. The built-in decimal style remains the most predictable choice for long or frequently changing procedures. Keep the custom design local to the short process; a global ol rule can surprise unrelated lists. Verify line wrapping does not let a long marker collide with item text.",
    ["Do not use a cyclic marker for ordered steps that may grow.", "Do not omit a fallback for values beyond the fixed set.", "Do not replace the semantic ordered list with decorative labels."],
    ["css/list-markers-and-counters", "html/ordered-list-numbering", "css/writing-mode-layout"])

add("image-set-density", "CSS image-set: offer resolution choices for decoration",
    "Serve a suitable background asset for dense displays without making essential content depend on it.",
    "The image-set function gives the browser multiple CSS image candidates with resolution descriptors. It is useful for decorative backgrounds on devices with different pixel densities. It does not provide alternative text or turn a CSS background into a content image.",
    "A case-map card has a purely decorative contour behind its readable heading. Supply an ordinary 1x URL first, then a candidate set with 1x and 2x files for browsers that support image-set. Keep a solid background color beneath the image so failed requests leave a usable card. The two paths in the sample are deployment assets, not files bundled by this content draft. Confirm their real dimensions, MIME types, cache headers, and response codes before reusing the rule. Test both display densities, offline loading, slow networks, reduced data modes where available, and print. Do not put evidence, a route, or a status label only in the background image; users who disable backgrounds, print in grayscale, or use assistive technology must still receive the information from HTML. A high-density screen does not guarantee the browser chooses the 2x file every time.",
    ".case-map { background-color: #e8f1f4; background-image: url('/assets/case-map-1x.webp'); background-size: cover; }\n@supports (background-image: image-set(url('/assets/case-map-1x.webp') 1x)) { .case-map { background-image: image-set(url('/assets/case-map-1x.webp') 1x, url('/assets/case-map-2x.webp') 2x); } }",
    "Resolution choice affects transfer size, decoding, and memory. Measure actual bytes and rendering on a slow device instead of assuming a 2x file is always worthwhile. image-set selects among candidates, but an individual failed request is not a dependable signal to retry the previous CSS declaration; the solid color is the resilient visual fallback. The background should be compressed and appropriately sized for its displayed area. If an image carries meaning, use HTML image markup with an appropriate text alternative and responsive source selection rather than hiding it in CSS. The card's title and actions must retain contrast over the chosen asset as well as over the plain color.",
    ["Do not use a CSS background for essential evidence or labels.", "Do not assume the browser will always choose the largest candidate.", "Do not ship illustrative asset paths without creating and checking the files."],
    ["css/backgrounds-and-decorative-images", "css/background-size-position", "html/responsive-images"])

add("wide-gamut-color-gate", "CSS color-gamut: add a wide-color accent behind an sRGB base",
    "Reserve Display P3 color for an optional accent and retain a checked sRGB presentation.",
    "The color-gamut media feature reports the approximate range of colors the browser and output device can display. A p3 query is a capability gate, not a test of whether a particular foreground and background pair has readable contrast.",
    "A case-status card uses a blue accent strip for visual grouping. Define the sRGB color first, then replace only the decorative strip when both the P3 color syntax and output capability are available. Keep the text color and status word independent of the accent. The sample uses nested feature and media queries to avoid sending a wide-gamut value to a parser or device that cannot use it. Review the final pixels on ordinary sRGB and P3 displays, in forced colors, and in print; software screenshots may be converted to another color space before anyone sees them. A bright P3 accent can clip or appear less saturated on other output paths. Never use color-gamut to classify the user's device quality or to decide whether an error message is displayed. Visual state must still have text and a noncolor cue.",
    ".case-status { border-inline-start: .35rem solid #1f7794; color: #153447; }\n@supports (color: color(display-p3 0 0 0)) { @media (color-gamut: p3) { .case-status { border-inline-start-color: color(display-p3 .08 .48 .66); } } }",
    "A flat color value is cheap to render. The cost lies in review across displays, color profiles, and forced-color settings. Because gamut support is approximate, the query is no proof that an exact color can be rendered without mapping. Measure contrast from the actual composited foreground and background, not the source channel values alone. The original sRGB border remains a full presentation when the enhanced rule does not apply. Use wide-gamut color for a modest decorative gain, not a second information system that disappears on common displays. Keep design tokens documented so later theme changes update both branches together.",
    ["Do not treat a P3 query as a contrast test.", "Do not encode status only in a wide-gamut accent.", "Do not omit an sRGB color before the enhanced declaration."],
    ["css/colors-and-contrast", "css/supports-feature-query", "css/dark-mode-and-forced-colors"])

add("oklch-palette-boundary", "CSS oklch: tune a surface color without guessing contrast",
    "Use a perceptual color model for a surface while verifying the rendered result.",
    "The oklch function describes a color with lightness, chroma, and hue channels. It gives designers a useful way to adjust a palette, but equal lightness values are not an accessibility guarantee and a requested color may need gamut mapping on the output device.",
    "A payment exception panel needs a restrained blue surface behind dark text. Start with a tested hex fallback, then place an oklch surface behind it when the function is supported. Keep the foreground explicit in both cases. The numerical lightness is a design input, not a contrast ratio: font weight, text size, alpha, backdrop, and display processing still determine readability. Compare normal text, links, focus rings, disabled controls, and dark-mode versions after the actual colors are computed. If the panel can sit over an image or translucent surface, test that composite rather than the flat token alone. Avoid generating an entire warning system by adding the same chroma amount to arbitrary hues; some requested colors fall outside the target display gamut and can map differently. Keep status wording in HTML so palette variation never removes meaning.",
    ".payment-exception { color: #163746; background: #eaf3f6; }\n@supports (background: oklch(95% .025 220)) { .payment-exception { background: oklch(95% .025 220); } }",
    "Color calculation has little performance cost. Validation cost grows with the number of themes, overlays, and component states that share the token. Check the computed color in the target browsers and run contrast measurements on the final pair; an oklch lightness percentage is not a WCAG score. Gamut mapping can alter high-chroma colors, so prefer restrained values for broad UI surfaces and review P3 and sRGB output separately. The hex fallback must remain acceptable on its own. A color surface can aid grouping, but it must not be the only error signal, especially in forced colors or monochrome print.",
    ["Do not read oklch lightness as a text contrast score.", "Do not assume a requested high-chroma color is rendered identically on every display.", "Do not remove the tested fallback or textual status."],
    ["css/colors-and-contrast", "css/color-mix-surfaces", "css/wide-gamut-color-gate"])

add("background-clip-text", "CSS background-clip text: keep a decorative headline readable",
    "Clip a gradient to headline glyphs only when the solid-color fallback is complete.",
    "Background-clip text paints an element's background through its text shapes. To reveal the background, the text fill must become transparent. That combination can hide words when the effect, gradient, or forced-color behavior differs from the design assumption.",
    "A public report headline may use a two-tone accent for a campaign page, while the actual heading remains ordinary HTML text. Start with a high-contrast solid color. In a supporting browser, apply a local gradient, clip it to the text, and make the glyph fill transparent. Restore a system text color in forced colors so the heading does not disappear when decorative backgrounds are suppressed. Test the heading against its real page background, on narrow lines, at high zoom, with background images disabled, and in print. A gradient that looks attractive on a large title can leave thin strokes too pale. Keep the gradient decorative: do not encode two separate statuses in its colors, and do not use a pseudo-element copy of the heading as the only text. If the enhanced effect fails, the fallback must still satisfy the design's information and contrast requirements.",
    ".report-hero__title { color: #164d68; }\n@supports (background-clip: text) { .report-hero__title { background: linear-gradient(90deg, #164d68, #276b85); background-clip: text; color: transparent; } }\n@media (forced-colors: active) { .report-hero__title { background: none; color: CanvasText; } }",
    "Clipping a small static headline is usually modest, but animated gradients or large text surfaces can add paint work. There is little reason to animate this effect in a data-heavy dashboard. The main risk is readability: transparent text depends on the clipped background being painted and on both gradient ends having sufficient contrast. Automated checks may not understand the full gradient, so inspect the palest segment of each glyph against the actual backdrop. Print and forced-color output deserve separate checks. Keep a solid text color before the enhanced rule and never make the CSS effect responsible for the heading's semantics or navigation target.",
    ["Do not set transparent text outside a guarded, working clipped-background rule.", "Do not assume every part of a gradient meets text contrast.", "Do not let forced-color mode erase the heading."],
    ["css/colors-and-contrast", "css/background-gradients-and-shadows", "css/forced-color-adjust-exceptions"])


assert len(specs) == 8
titles = {path: row["title"] for path, row in by_path.items()}
titles.update({item["path"]: item["title"] for item in specs})
titles[quiz_path] = "CSS type, color, and asset decisions quiz"


def links(paths):
    assert all(path in titles for path in paths), paths
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in paths
    ) + "</ul>"


hub = by_path[hub_path]
hub["data"]["modules"].append({
    "title": "Type, color, and assets",
    "summary": "Check font axes, marker fallbacks, image candidates, color gamut, and clipped decoration.",
    "lessons": [item["path"] for item in specs],
})
hub["body"] += "<h2>Type, color, and assets</h2>" + links([item["path"] for item in specs])
hub["updated_at"] = stamp

for index, item in enumerate(specs):
    row = copy.deepcopy(by_path["css/selectors-and-cascade"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + item["path"])),
               path=item["path"], title=item["title"], summary=item["summary"],
               subject="css-reference", sort_order=24070 + index,
               status="published", published_at=stamp, created_at=stamp,
               updated_at=stamp)
    row["tags"] = ["css", "reference", "web"]
    row["data"] = {
        "kind": "tutorial", "reading_minutes": 5,
        "author_path": "authors/aitrove-editorial", "subject_root": "css/css-tutorial",
        "section_path": hub_path, "content_format": "html", "seo_ready": True,
        "related": [{"path": target, "title": titles[target]} for target in item["related"]],
    }
    row["body"] = (
        f"<p>{html.escape(item['definition'])}</p><h2>When to use it</h2>"
        f"<p>{html.escape(item['decision'])}</p>"
        f'<pre><code class="language-css">{html.escape(item["sample"])}</code></pre>'
        f"<h2>Cost and verification</h2><p>{html.escape(item['cost'])}</p>"
        + "<h3>Common Mistakes</h3><ul>"
        + "".join(f"<li>{html.escape(mistake)}</li>" for mistake in item["mistakes"])
        + "</ul><h2>Connected lessons</h2>" + links([hub_path, *item["related"]])
    )
    rows.append(row)

for source, targets in {
    "css/font-loading": ["css/variable-font-weight-range", "css/font-optical-sizing-check", "css/font-synthesis-boundary"],
    "css/list-markers-and-counters": ["css/counter-style-fallback"],
    "css/backgrounds-and-decorative-images": ["css/image-set-density", "css/background-clip-text"],
    "css/colors-and-contrast": ["css/wide-gamut-color-gate", "css/oklch-palette-boundary"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Further type and color decisions</h2>" + links(targets)
    row["data"].setdefault("related", []).extend(
        {"path": target, "title": titles[target]} for target in targets
    )
    row["updated_at"] = stamp

questions = [
    ("What should an @font-face weight range reflect?", ["Weights actually present in the file", "Every possible CSS weight", "Only the title's current size"], 0, "The descriptor must match the supplied font's supported range."),
    ("When can font-optical-sizing auto change glyph drawings?", ["When the selected font has an optical-size axis", "Whenever a page has media queries", "Only when text is an image"], 0, "The font needs an opsz axis for optical sizing to act."),
    ("What risk follows font-synthesis-weight none with no real bold face?", ["Emphasis can lose its visual weight", "The browser creates a stronger bold", "HTML strong becomes invalid"], 0, "Disabling synthetic weight does not supply a missing face."),
    ("What happens after a fixed counter style runs out of symbols?", ["Its fallback style represents later values", "The first symbol must repeat", "The list stops being ordered"], 0, "The fallback descriptor handles values outside the finite sequence."),
    ("What information belongs in HTML rather than a CSS background?", ["An evidence image with meaning", "A decorative contour", "A purely visual texture"], 0, "Meaningful images need markup and an appropriate text alternative."),
    ("What does image-set let the browser choose?", ["Among declared image candidates", "The text alternative", "The server's legal retention policy"], 0, "image-set offers resolution or format candidates for CSS images."),
    ("What does a p3 color-gamut query establish?", ["Approximate wide-color output capability", "Accessible contrast for every pair", "Exact color reproduction in print"], 0, "Gamut support is approximate and does not measure contrast."),
    ("Why keep an sRGB value before a P3 accent?", ["It is the complete baseline on ordinary displays", "It forces P3 on unsupported devices", "It removes the need for text labels"], 0, "The sRGB presentation must stand alone when the enhancement does not apply."),
    ("What is oklch lightness by itself?", ["A color-model channel", "A WCAG contrast ratio", "A printer profile"], 0, "Contrast depends on the final foreground and background combination."),
    ("Why test an oklch color on the target display?", ["Gamut mapping can alter the requested result", "CSS forbids all chroma", "The syntax changes HTML semantics"], 0, "Out-of-gamut requests can be mapped to displayable colors."),
    ("What can make background-clip text disappear?", ["Transparent fill without a painted clipped background", "A solid fallback color", "A semantic heading element"], 0, "The transparent text depends on the clipped background being visible."),
    ("What should a clipped-gradient heading use in forced colors?", ["A readable system text color", "Only a transparent glyph fill", "No heading text"], 0, "A system color keeps the heading visible when decorative backgrounds are suppressed."),
]
assert len(questions) == 12
quiz = copy.deepcopy(by_path["quizzes/css-advanced"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
            path=quiz_path, title=titles[quiz_path],
            summary="Twelve checks on font axes, list markers, image candidates, and color output.",
            sort_order=3107, status="published", published_at=stamp,
            created_at=stamp, updated_at=stamp)
quiz["data"] = {
    "subject_root": "css/css-tutorial", "section_path": "css/quizzes",
    "content_format": "html", "author_path": "authors/aitrove-editorial",
    "seo_ready": True, "duration_minutes": 12,
    "related": [{"path": target, "title": titles[target]} for target in [
        "css/variable-font-weight-range", "css/counter-style-fallback",
        "css/image-set-density", "css/oklch-palette-boundary"]],
    "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                       answer=(answer - index % 3) % 3, explanation=explanation)
                  for index, (prompt, options, answer, explanation) in enumerate(questions)],
}
quiz["body"] = (
    "<p>Check which presentation choices require a real font, image asset, output capability, or fallback. Each question has one answer and an explanation.</p>"
    "<h2>Review the decisions</h2>" + links([item["path"] for item in quiz["data"]["related"]])
    + "<h2>Other checks</h2>" + links(["css/quizzes", "quizzes/css-modern-behavior"])
    + "<h3>Common Mistakes</h3><ul><li>Do not confuse a color channel with measured contrast.</li>"
    "<li>Do not assume an asset path in a lesson points to a deployed file.</li></ul>"
)
rows.append(quiz)
quiz_hub = by_path["css/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Type and color check</h2>" + links([quiz_path])
quiz_hub["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_quizzes": 1,
                  "total_records": len(rows)}))
