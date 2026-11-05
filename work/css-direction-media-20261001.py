"""Add eight focused CSS decisions and a linked review quiz."""

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
quiz_path = "quizzes/css-direction-media"
specs = []


def add(slug, title, summary, definition, decision, sample, cost, mistakes, related):
    path = "css/" + slug
    assert path not in by_path
    specs.append(dict(path=path, title=title, summary=summary, definition=definition,
                      decision=decision, sample=sample, cost=cost, mistakes=mistakes,
                      related=related))


add(
    "dir-selector-inherited",
    "CSS :dir(): respond to computed text direction",
    "Style a direction-aware document without assuming every descendant carries dir.",
    "The :dir() pseudo-class matches an element by its text direction, including direction inherited from an ancestor or resolved from dir=auto. An attribute selector such as [dir=rtl] only finds an explicit attribute. CSS direction changes layout behavior but does not make :dir() match a new semantic direction; put the correct direction in HTML.",
    "A case review page displays an Arabic customer note inside an otherwise left-to-right interface. The note's HTML establishes its direction; a nested action row inherits that direction even though it has no dir attribute. A :dir(rtl) rule adjusts the row's border and alignment, while logical padding and margin work for either direction. Test an Arabic note, an English note, a mixed numeric identifier, and a note whose dir=auto resolves differently after its text changes. Do not reverse characters with transforms or reorder controls merely for visual symmetry. Keep numbers, links, and punctuation readable in mixed-script content, and verify with actual localized strings rather than a Latin placeholder. A language tag and a direction attribute answer different questions. The former helps pronunciation and typographic conventions; the latter establishes bidirectional layout. The selector is useful only after the document has the right semantics.",
    '.case-note { padding-inline: 1rem; border-inline-start: .25rem solid #396c82; }\n.case-note:dir(rtl) .case-note__actions { text-align: start; border-inline-start: .15rem solid #819aa5; }\n.case-note:dir(ltr) .case-note__actions { text-align: start; border-inline-start: .15rem solid #396c82; }',
    "Selector matching is cheap; the cost is translation and bidirectional testing. A stylesheet cannot infer the intended reading direction from a username or code token. Keep the HTML dir value correct, especially when a component receives user-provided text. A [dir=rtl] shortcut misses inherited and auto-resolved cases, while a global direction override can disturb unrelated form controls. The CSS sample deliberately uses logical borders so its geometry follows writing direction without duplicate left/right coordinates. Verify keyboard order and screen reader output separately from painted alignment. Direction-aware decoration must never be the only indication of who authored a note or what language it contains.",
    ["Do not treat [dir=rtl] as equivalent to :dir(rtl).", "Do not expect CSS direction to establish the semantic direction matched by :dir().", "Do not use transforms to fake right-to-left reading order."],
    ["css/writing-mode-layout", "css/logical-properties", "css/language-selector-typography", "html/language-and-direction"],
)

add(
    "text-orientation-vertical",
    "CSS text-orientation: choose glyph posture in vertical text",
    "Keep vertical labels legible when Latin and East Asian characters share a line.",
    "text-orientation controls how glyphs are drawn in a vertical writing mode. The mixed value generally leaves upright scripts upright and turns horizontal-script glyphs sideways; upright asks every character to remain upright. It is not a substitute for writing-mode, and a rotated horizontal box does not reproduce vertical text layout.",
    "An archive index has compact Japanese section labels containing short Latin inventory codes. The page uses writing-mode: vertical-rl for the index only. The default mixed orientation keeps the code as a readable sideways run, while a short numeric badge is set upright because its digits are intended as a vertical marker. Compare both with a real translation and longer identifiers; upright Latin letters can become a stack of separate characters and consume much more block space. Test line breaks, punctuation, selection, high zoom, and a fallback font with the actual scripts used. The surrounding document should keep its normal reading direction. A vertical title can be meaningful, but a decorative sidebar with a long sentence often imposes unnecessary reading work. If the label is essential navigation, provide enough room and keep the DOM sequence sensible for keyboard and assistive technology. Do not rotate a horizontal sentence merely to save width.",
    '.archive-index { writing-mode: vertical-rl; text-orientation: mixed; max-block-size: 18rem; }\n.archive-index__badge { text-orientation: upright; font-weight: 700; }\n.archive-index a:focus-visible { outline: 3px solid #1c5e87; outline-offset: 3px; }',
    "Vertical text can change intrinsic sizes and wrapping; check narrow containers and fallback fonts before fixing a height. The browser performs ordinary text layout, so the property itself is not a performance concern. The larger cost is QA across scripts, font coverage, punctuation, and selection behavior. Do not set upright on a long Latin code without checking its length. A rotated transform may visually resemble a vertical label, but it keeps horizontal layout geometry and can produce awkward clipping and focus outlines. Text-orientation applies only in vertical writing modes. Keep the navigation label understandable when styles do not load.",
    ["Do not expect text-orientation to create a vertical writing mode by itself.", "Do not use upright for arbitrary long Latin identifiers.", "Do not rotate the entire navigation box and assume layout and reading order follow."],
    ["css/writing-mode-layout", "css/logical-properties", "css/language-selector-typography", "html/language-and-direction"],
)

add(
    "text-emphasis-marks",
    "CSS text-emphasis: add a typographic cue without hiding meaning",
    "Use emphasis marks where the language and font make them readable.",
    "text-emphasis paints marks near characters, commonly in East Asian typography. The marks are presentation, not a replacement for meaningful wording or structural emphasis. Their position depends on writing mode, and narrow line spacing may need adjustment to prevent marks from colliding with adjacent text.",
    "A bilingual catalog uses emphasis marks on a short Japanese caution phrase. The phrase still says what action is required in words, so a reader who does not see the marks loses no instruction. A strong element in the HTML carries the semantic emphasis; CSS adds dots only within the Japanese copy scope. Review horizontal and vertical editions, ruby annotations, punctuation, multiple-line wraps, and the actual font shipped with the page. A mark above a horizontal line may compete with ruby text, so choose one annotation method for a given phrase rather than stacking visual cues without inspection. The sample gives the caution line extra leading, which must be measured with real translated text at high zoom. Avoid applying marks to a whole paragraph: the result becomes noisy, and the line-box cost grows across many lines. If the product relies on a warning, preserve a text label or other semantic signal that survives print, forced colors, and missing CSS.",
    '.catalog-copy:lang(ja) strong { text-emphasis: filled dot #803a42; text-emphasis-position: over right; }\n.catalog-copy:lang(ja) { line-height: 1.8; }\n@media print { .catalog-copy:lang(ja) strong { text-emphasis-color: currentColor; } }',
    "The marks are inexpensive to paint, but line spacing and font fallback affect layout. Test whether a different typeface moves or obscures them. Browser and font rendering can differ, and a forced-colors mode may replace authored colors. Keep the original text meaningful without decoration. CSS cannot make a strong element semantically correct if the author highlighted the wrong phrase. Reserve the effect for short runs and inspect line breaks at the widths actually used by readers. If ruby is present, verify its placement before choosing over or under emphasis. The visual mark should aid reading, not become the only safety cue.",
    ["Do not use emphasis marks as the sole warning.", "Do not apply marks to long blocks without checking line spacing.", "Do not stack marks and ruby annotation without reviewing collisions."],
    ["css/language-selector-typography", "css/readable-type", "css/writing-mode-layout", "html/inline-text-meaning"],
)

add(
    "image-rendering-pixel-art",
    "CSS image-rendering: preserve a pixel map's hard edges",
    "Upscale deliberately blocky images without treating interpolation as compression.",
    "image-rendering chooses the scaling algorithm for an image. pixelated is suitable when enlarged source pixels should remain visibly square. It does not change image dimensions in the file, remove bytes from the transfer, or improve a blurry photograph. Scoping matters because the property can be inherited by descendant images.",
    "A dispatch dashboard includes a 32-by-32 status map that is intentionally drawn on a pixel grid. The map is displayed at 192-by-192 CSS pixels, an integer sixfold enlargement, so pixelated rendering preserves the original cells. Its neighboring photographic evidence retains ordinary interpolation. Include actual image dimensions in HTML to reserve space, and write alt text describing the map's meaning rather than its texture. Test the image at browser zoom levels that make the effective scale noninteger; edge treatment can vary and may not look as crisp as the nominal sixfold case. If the graphic contains small text, produce a larger source image instead of relying on nearest-neighbor scaling. High-density screens and print output also deserve inspection. A pixelated image is a design choice for discrete graphics, not a blanket performance optimization. Serve an appropriately sized source when visual detail matters.",
    '.dispatch-map__raster { inline-size: 12rem; block-size: 12rem; image-rendering: pixelated; }\n.dispatch-photo { max-inline-size: 100%; block-size: auto; image-rendering: auto; }',
    "The rendering hint is cheap, but an oversized decoded bitmap still consumes memory and network bandwidth. The 32-by-32 source shown here is small; the 192-by-192 display size changes presentation only. Keep the rule on the specific raster instead of a container, or other descendant images may inherit the pixel treatment. Check zoom and device scale because integer CSS scaling does not guarantee integer device-pixel scaling. If users must inspect fine evidence, provide the proper resolution and an accessible description. A pixelated thumbnail cannot reconstruct detail that the source never contained.",
    ["Do not apply pixelated to photographs or all images in a card.", "Do not assume image-rendering reduces transfer size.", "Do not expect perfect square pixels at every zoom level."],
    ["css/image-fit-and-aspect", "css/image-set-density", "html/responsive-images", "html/inline-svg"],
)

add(
    "font-variation-custom-axis",
    "CSS font-variation-settings: use a verified custom axis",
    "Set an axis only after inspecting the font file and its declared range.",
    "font-variation-settings is the low-level route to variable-font axes. Use font-weight, font-style, font-width, and font-optical-sizing for their registered roles when possible. A custom axis tag is four characters and case-sensitive; a guessed tag or out-of-range value may have no useful effect.",
    "A licensed annotation typeface offers a custom grade axis named GRAD, with the range and value 40 confirmed from that particular file's metadata. The annotation label needs a slightly heavier stroke without changing its width, so the component sets the custom axis while ordinary font-weight remains a high-level property. The asset path in the sample is illustrative and must be replaced with a real font carrying that axis before release. Verify the axis in the shipped binary, its license, fallback appearance, and glyph coverage for localized text. Test regular and bold labels, because a low-level registered wght setting could override font-weight even if placed in another rule. If a later rule changes font-variation-settings, it replaces the entire axis list; redeclare all needed axes or coordinate through custom properties. Do not animate grade simply because the file permits it: repeated glyph rasterization may cost more than the small visual gain, and motion can distract from the annotation itself.",
    '@font-face { font-family: "Annotation Axis"; src: url("/assets/annotation-axis.woff2") format("woff2"); font-weight: 300 700; }\n.annotation-label { font-family: "Annotation Axis", sans-serif; font-weight: 520; font-variation-settings: "GRAD" 40; }\n.annotation-label--quiet { font-variation-settings: "GRAD" 0; }',
    "A variable font can reduce the need for separate static files, but the actual file size and subset strategy determine transfer cost. The illustrative asset is not present in this repository. Do not publish the example as a working feature until that licensed file is supplied and its GRAD range verified. Axis values outside a font's design range can be clamped, and a fallback font will ignore the custom setting. Validate in the target browser and inspect actual glyph output, not only computed CSS. Avoid setting registered axes through this low-level property when a dedicated CSS property can express the intent; that prevents confusing precedence during maintenance.",
    ["Do not invent a custom axis or its range from the CSS alone.", "Do not use low-level wght to fight an existing font-weight rule.", "Do not assume a fallback font responds to GRAD."],
    ["css/variable-font-weight-range", "css/font-optical-sizing-check", "css/font-loading", "css/unicode-range-font-subsets"],
)

add(
    "background-blend-layer-order",
    "CSS background-blend-mode: keep the layer order explicit",
    "Blend decorative backgrounds while preserving text contrast and a plain fallback.",
    "background-blend-mode blends an element's background image layers with one another and its background color. It does not blend the element's text with neighboring elements; that is a different compositing problem. A comma-separated mode list corresponds to the background-image layer list, so layer order must be reviewed together.",
    "A maintenance notice uses two CSS gradients over a flat blue background. The top gradient adds a subtle highlight and the second adds a darker edge; neither carries information. The text and action link remain readable against the whole result. Keep a solid background-color before the gradient declarations so an engine that ignores blending still has a usable panel. Test the palest and darkest parts of the surface, not just the center. A background image can fail to load or be disabled, and forced-colors modes may discard authored decoration. Because this design uses generated gradients, it adds no image request, though the browser still has to paint the composed layers. Do not use blend mode to rescue low-contrast text on a photograph; crop, overlay, or place the text on a solid surface instead. The rendered composite can vary with the color values behind it, so a small theme change requires contrast review rather than an assumption that the mode remains safe.",
    '.maintenance-note { color: #fff; background-color: #173f56; background-image: linear-gradient(135deg, rgb(255 255 255 / 18%), transparent 55%), linear-gradient(0deg, rgb(0 0 0 / 25%), transparent 70%); background-blend-mode: screen, multiply; padding: 1rem; }\n@media (forced-colors: active) { .maintenance-note { background-image: none; border: 1px solid CanvasText; } }',
    "Each extra background layer adds paint work; ordinary small cards are unlikely to be a bottleneck, but large scrolling surfaces should be profiled if effects pile up. No network request is added by a gradient. The comma order is easy to break when a designer adds a new image layer but leaves the mode list unchanged; browsers repeat or trim mode values to match the layers. Check the actual composite after any such edit. Text contrast is judged against the final painted background, not the raw base color. Preserve a solid base and ensure the notice is still understandable when decorative images are absent.",
    ["Do not confuse background-blend-mode with mix-blend-mode.", "Do not add a background layer without checking its corresponding mode.", "Do not assume base-color contrast proves contrast over every blended region."],
    ["css/mix-blend-mode-boundary", "css/backgrounds-and-decorative-images", "css/colors-and-contrast", "css/dark-mode-and-forced-colors"],
)

add(
    "fullscreen-media-state",
    "CSS :fullscreen: lay out media after the browser enters full screen",
    "Style the actual full-screen element and keep an exit path visible.",
    "The :fullscreen pseudo-class matches an element currently in full-screen mode. It does not enter that mode; a user action and the Fullscreen API or native media control do that. CSS should target the element that was actually requested, which might be a player wrapper rather than the video inside it.",
    "A training player places a video, transcript link, and custom controls in one wrapper. Request full screen on that wrapper when the user presses its explicit button, then let CSS give the player a dark surface and fit the video within the available space. If the native video control enters full screen on the video element instead, a wrapper:fullscreen rule will not match; test both paths in the actual product. Keep caption text and the exit control visible, respect safe areas, and verify that Escape and the on-screen button leave full screen. Test pointer, keyboard, touch, orientation changes, a denied request, and a browser that does not support the chosen flow. The CSS cannot guarantee full-screen access or capture errors from the API. Do not use a fixed pixel height based on one laptop screenshot; the available viewport and browser controls vary. The transcript link remains useful outside full screen even when captions are present.",
    '.training-player:fullscreen { display: grid; place-items: center; padding: 1rem; background: #081b26; color: #fff; }\n.training-player:fullscreen video { max-inline-size: 100%; max-block-size: 85vh; }\n.training-player:fullscreen :focus-visible { outline: 3px solid #f4c65f; outline-offset: 3px; }',
    "The selector has little cost. Large decoded video frames, overlays, and control updates dominate full-screen performance. An 85vh maximum is only a starting point; test captions, safe areas, and browser chrome on phones and tablets. A wrapper that contains controls can keep them in the full-screen element, while controls outside it may disappear from view. Full-screen activation and exit belong in application behavior, not CSS. Verify focus after entering and leaving, including the denial path, and do not hide the browser's own escape affordance. A full-screen paint change cannot repair missing captions or a broken video source.",
    ["Do not expect :fullscreen to request full screen.", "Do not style a wrapper if the video element is the actual full-screen target.", "Do not let custom controls or captions become unreachable in full screen."],
    ["css/caption-cue-presentation", "css/focus-visible", "html/video-captions", "html/video-playsinline"],
)

add(
    "print-widows-orphans",
    "CSS widows and orphans: keep short print paragraphs together",
    "Set minimum line counts around a page break, then inspect real print output.",
    "orphans sets the minimum number of lines from a paragraph that should remain at the bottom of a page or column; widows sets the minimum at the top of the next fragment. These are fragmentation hints for line boxes, not a way to keep an entire section together or control screen layout.",
    "An incident report is exported to paper for a review meeting. A paragraph with seven lines would read poorly if one line landed alone at a page boundary, so the print stylesheet requests two lines on each side of a break. A nearby heading has a separate break-after rule so it is not stranded from its first paragraph. Test actual printer previews with the final font, page margins, and long localized paragraphs. A browser may move more text than expected, and some print engines handle fragmentation differently. If the report contains tables, figures, or a page-sized block, widows and orphans will not solve those layout constraints. Keep a plain readable result if the hint is ignored. Do not force every paragraph to break-inside: avoid; that can create large blank spaces and may still fail when a paragraph is taller than a page. For a short receipt, the output may be simpler if the content is restructured rather than layering many print rules onto it.",
    '@media print { .incident-report p { orphans: 2; widows: 2; } .incident-report h2 { break-after: avoid; } .incident-report { color: #000; background: #fff; } }',
    "These declarations do not add runtime network or script cost. Their practical cost is page-layout QA across print engines and content lengths. A different font metric can shift line breaks and invalidate a preview taken before assets load. Wait for fonts in a print test, then inspect page boundaries rather than only the first page. Use modest minimums: demanding four or five lines around every break may create excessive whitespace. The browser may not honor the hint in every fragmentation situation, so the text must remain coherent without it. This rule affects print and other fragmented contexts, not the ordinary scrolling page.",
    ["Do not confuse widows and orphans with break-inside: avoid.", "Do not expect them to keep a whole section on one page.", "Do not approve print layout after checking only the first page."],
    ["css/print-styles", "css/page-rule-print-contract", "css/fragmentation-break-inside", "html/print-stylesheet-media"],
)


assert len(specs) == 8
titles = {path: row["title"] for path, row in by_path.items()}
titles.update({item["path"]: item["title"] for item in specs})
titles[quiz_path] = "CSS direction, type, and media decisions quiz"


def links(paths):
    assert all(path in titles for path in paths), paths
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in paths
    ) + "</ul>"


hub = by_path[hub_path]
hub["data"]["modules"].append({
    "title": "Direction, glyphs, and media paint",
    "summary": "Check direction-aware styling, vertical type, image scaling, blending, full screen, and print breaks.",
    "lessons": [item["path"] for item in specs],
})
hub["body"] += "<h2>Direction, glyphs, and media paint</h2>" + links([item["path"] for item in specs])
hub["updated_at"] = stamp

for index, item in enumerate(specs):
    row = copy.deepcopy(by_path["css/selectors-and-cascade"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + item["path"])),
               path=item["path"], title=item["title"], summary=item["summary"],
               subject="css-reference", sort_order=24200 + index,
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
    "css/writing-mode-layout": ["css/dir-selector-inherited", "css/text-orientation-vertical"],
    "css/language-selector-typography": ["css/text-emphasis-marks"],
    "css/image-fit-and-aspect": ["css/image-rendering-pixel-art"],
    "css/variable-font-weight-range": ["css/font-variation-custom-axis"],
    "css/mix-blend-mode-boundary": ["css/background-blend-layer-order"],
    "css/caption-cue-presentation": ["css/fullscreen-media-state"],
    "css/print-styles": ["css/print-widows-orphans"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Further rendering decisions</h2>" + links(targets)
    row["data"].setdefault("related", []).extend(
        {"path": target, "title": titles[target]} for target in targets
    )
    row["updated_at"] = stamp

questions = [
    ("What can :dir(rtl) match that [dir=rtl] misses?", ["Inherited or auto-resolved right-to-left direction", "Only a CSS transform", "Only an explicit class name"], 0, "The pseudo-class follows semantic direction, not only the attribute on that element."),
    ("What must exist before text-orientation changes glyph posture?", ["A vertical writing mode", "A full-screen element", "A blend mode"], 0, "It operates within vertical text layout."),
    ("Why keep a warning understandable without text-emphasis?", ["The marks are only presentation", "The marks submit form data", "The marks choose a font file"], 0, "Meaning must survive missing or altered styling."),
    ("What does image-rendering: pixelated change?", ["The scaling appearance", "The transferred file size", "The image alt text"], 0, "It is a rendering hint, not an optimizer."),
    ("Why verify the GRAD axis in a font file?", ["Custom tags and ranges are font-specific", "CSS creates any missing axis", "Every font has GRAD"], 0, "A custom axis is useful only when that file actually provides it."),
    ("Which property should usually set a registered weight axis?", ["font-weight", "background-blend-mode", "text-orientation"], 0, "High-level font properties communicate registered-axis intent."),
    ("What must be reviewed after adding a background image layer?", ["The corresponding blend-mode order and final contrast", "Only the DOM focus order", "Only the font license"], 0, "The mode list follows the image layer list."),
    ("What does :fullscreen do on its own?", ["Match an element already in full screen", "Request full-screen access", "Start video playback"], 0, "Entering full screen is an application or native-control action."),
    ("Why might .player:fullscreen fail to style a native full-screen video?", ["The video, not the wrapper, may be the matching element", "The video has no pixels", "The selector always matches every ancestor"], 0, "Target the element that actually entered full screen."),
    ("What do widows and orphans govern?", ["Minimum paragraph lines around a fragment break", "The number of columns on screen", "The entire report's page count"], 0, "They guide paragraph line fragmentation."),
    ("What should a print review inspect?", ["Every relevant page boundary with final fonts", "Only the first screen viewport", "Only the CSS parse result"], 0, "Font metrics and content length change page breaks."),
    ("Which fallback is useful under a blended notice?", ["A readable solid background color", "An invisible text color", "A forced fixed height"], 0, "The notice should remain usable without decorative layers."),
]
assert len(questions) == 12
quiz = copy.deepcopy(by_path["quizzes/css-advanced"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
            path=quiz_path, title=titles[quiz_path],
            summary="Twelve checks on direction, typography, image scaling, blending, full screen, and print.",
            sort_order=3120, status="published", published_at=stamp,
            created_at=stamp, updated_at=stamp)
quiz["data"] = {
    "subject_root": "css/css-tutorial", "section_path": "css/quizzes",
    "content_format": "html", "author_path": "authors/aitrove-editorial",
    "seo_ready": True, "duration_minutes": 12,
    "related": [{"path": target, "title": titles[target]} for target in [
        "css/dir-selector-inherited", "css/image-rendering-pixel-art",
        "css/background-blend-layer-order", "css/print-widows-orphans"]],
    "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                       answer=(answer - index % 3) % 3, explanation=explanation)
                  for index, (prompt, options, answer, explanation) in enumerate(questions)],
}
quiz["body"] = (
    "<p>Check which rendering decisions belong in CSS and which require sound document structure, assets, or application behavior.</p>"
    "<h2>Review the decisions</h2>" + links([item["path"] for item in quiz["data"]["related"]])
    + "<h2>Other checks</h2>" + links(["css/quizzes", "quizzes/css-native-states"])
    + "<h3>Common Mistakes</h3><ul><li>Do not mistake a paint hint for a content or behavior guarantee.</li>"
    "<li>Do not publish a font-axis sample before verifying the actual file.</li></ul>"
)
rows.append(quiz)
quiz_hub = by_path["css/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Direction and media check</h2>" + links([quiz_path])
quiz_hub["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_quizzes": 1,
                  "total_records": len(rows)}))
