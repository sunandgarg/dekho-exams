"""Add applied CSS lessons on typography, fragmentation, and top-layer state."""

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
quiz_path = "quizzes/css-type-overlay"
specs = []


def add(slug, title, summary, definition, decision, sample, cost, mistakes, related):
    path = "css/" + slug
    assert path not in by_path
    specs.append(dict(path=path, title=title, summary=summary,
                      definition=definition, decision=decision, sample=sample,
                      cost=cost, mistakes=mistakes, related=related))


add(
    "unicode-range-font-subsets",
    "CSS unicode-range: request only the font subset a page uses",
    "Declare script-specific font files without pretending that a range splits a font file.",
    "The unicode-range descriptor limits which characters an @font-face resource can supply. A browser can avoid fetching a face when the page uses none of its declared characters. The descriptor does not split one large font file into smaller files; the files must already be subsetted.",
    "A case registry has Latin interface copy and a separate Greek-language archive. Ship two licensed WOFF2 subsets under one family, each with a range matching glyphs actually present in its file. Keep a system fallback for missing glyphs, punctuation, and a failed font request. The sample paths are deployment placeholders; replace them with real, audited files before using the rule. Inspect the network panel on a Latin-only route, then on a Greek route, and check which resources load. Also test a mixed-language record, accented names, search results inserted after initial render, and font loading under a slow connection. A broad range that claims a glyph absent from the file can send the browser through poor fallback. Language tags remain necessary for pronunciation and text processing; font selection alone does not establish language. Do not infer that a page needs a script merely from its locale setting, because the actual text may contain names or citations from several scripts.",
    '@font-face { font-family: "Registry Sans"; src: url("/assets/registry-latin.woff2") format("woff2"); unicode-range: U+0000-024F; font-display: swap; }\n@font-face { font-family: "Registry Sans"; src: url("/assets/registry-greek.woff2") format("woff2"); unicode-range: U+0370-03FF; font-display: swap; }\n.registry-copy { font-family: "Registry Sans", system-ui, sans-serif; }',
    "The possible win is fewer transferred font bytes on pages using one script. The cost is additional files, range maintenance, and the risk of gaps when editorial copy changes. A glyph used from a range can trigger a download of that entire face, so splitting a tiny file into dozens of requests may be worse. Measure transfer size and layout shift with representative routes rather than assuming every subset improves speed. Verify the license permits the files and any subsetting operation. Match the declared font weight and style to the files; fake bold or italic is a separate typographic failure. If the fonts are unavailable, the system fallback must preserve readable line lengths and controls.",
    ["Do not expect unicode-range to split a monolithic font automatically.", "Do not claim code points that the referenced file cannot render.", "Do not omit a usable fallback or the real font license."],
    ["css/font-loading", "css/font-display-policy", "css/variable-font-weight-range", "html/language-and-direction"],
)

add(
    "ligatures-in-identifiers",
    "CSS font-variant-ligatures: keep identifiers visually literal",
    "Disable joined glyph forms where a record identifier must be inspected character by character.",
    "Font ligatures can render multiple source characters as one combined glyph. The font-variant-ligatures property controls these substitutions; none disables them for the selected text. It does not rewrite the DOM string, change copying, or make similar-looking Unicode characters safe to compare.",
    "A fraud review screen displays transaction IDs and short diagnostic fragments. Operators compare those strings against printed records, so avoid a font turning an adjacent character pair into a single ornamental form. Apply none only to the identifier and code surfaces, not to every paragraph on the site. A monospaced fallback keeps spacing predictable when the preferred face is unavailable. Test IDs with pairs such as fi and fl, mixed letters and digits, copied text, high zoom, and a fallback font. A visual transcription check still needs grouping, adequate size, and a way to copy the exact value. Do not substitute typographic styling for a checksum or a machine comparison. A screen reader reads the source text, not the ligature glyph; the underlying identifier should remain a plain text node and not be recreated by pseudo-elements. When an identifier is long, allow a controlled wrap instead of clipping the final characters.",
    '.transaction-id, .diagnostic-code { font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-variant-ligatures: none; overflow-wrap: anywhere; }\n.case-note { font-variant-ligatures: normal; }',
    "The rendering cost is negligible. Restricting the rule reduces maintenance work because prose can retain the font's intended shaping. Test the actual font files: a face without ligatures will show no visual difference, while a decorative coding font may change several pairs. Disabling all ligatures across a script that needs contextual shaping can damage readability; keep the selector narrow. The copied bytes are unchanged, so this CSS cannot detect a homoglyph, verify a transaction, or fix bad source data. Use semantic labels and exact machine values for audit workflows, with CSS only improving human inspection.",
    ["Do not disable ligatures globally on multilingual prose.", "Do not confuse a visual join with a changed identifier value.", "Do not let a long ID disappear behind overflow clipping."],
    ["css/font-shorthand-stack", "css/readable-type", "css/tab-size-code-blocks", "html/preformatted-code-and-output"],
)

add(
    "language-selector-typography",
    "CSS :lang(): style text from its declared language",
    "Use language state from the document for script-sensitive presentation rules.",
    "The :lang() pseudo-class matches an element according to its determined content language, including a language inherited from an ancestor. It is not merely an attribute selector for elements carrying their own lang attribute. CSS styling cannot declare the language for assistive technology; the document must do that.",
    "A multilingual incident note contains a French quotation inside an English report. The HTML marks the quotation's language, and the style gives that text appropriate quote marks and automatic hyphenation where a dictionary is available. A nested title or emphasized phrase can match through inherited language. Check the real quote markup, not a decorative pair of pseudo-element characters, because nested quotations and copy behavior matter. Test French regional variants, words without a hyphenation dictionary, an untagged quotation, and a translated page where the outer document language changes. The reading order and words must remain correct without CSS. Do not apply a site-wide script font merely because one region has a different language; Unicode coverage and fallback still need inspection. CSS can improve presentation once the document identifies the language, but it cannot repair a wrong lang value or tell a speech engine how to pronounce an unmarked phrase.",
    '.incident-quote:lang(fr) { hyphens: auto; }\n.incident-quote q:lang(fr) { quotes: "« " " »" "‹ " " ›"; }\n.incident-quote:lang(en) { hyphens: manual; }',
    "The selector cost is small; the larger risk is editorial language metadata and browser dictionary availability. Automatic hyphenation can produce different line breaks across systems and may need an explicit minimum measure or manual review for headings. Quote glyphs are presentational, so verify how the browser handles nested q elements and copied text. A CSS rule cannot translate text. Preserve a readable fallback when :lang() or a language-specific hyphenation dictionary is unavailable. Do not rely on a language selector to choose an external font subset without testing the actual glyph mix in translated names and citations.",
    ["Do not use :lang() in place of an HTML lang declaration.", "Do not assume every browser has a hyphenation dictionary for the selected language.", "Do not type duplicate decorative quote characters into the source text."],
    ["css/hyphenation-and-language", "css/writing-mode-layout", "css/unicode-range-font-subsets", "html/language-and-direction"],
)

add(
    "text-transform-display-case",
    "CSS text-transform: change display case without corrupting source data",
    "Reserve visual uppercase for short controlled labels, not names, codes, or stored values.",
    "Text-transform changes the rendered case of text. It does not change the source string, form value, or server record. Case mappings can depend on language, and browser support for some language-specific transformations differs.",
    "An operations dashboard uses compact state labels such as pending review and evidence sealed. Uppercase can help separate these controlled labels from nearby prose, provided the size, tracking, and contrast remain legible. Keep the stored state machine key separate from the displayed localized phrase. Test a translated label with dotted and dotless i, a long label that wraps, a screen reader, and high zoom. Never apply uppercase to a person's name, a case-sensitive identifier, an email address, or a quotation merely to fit the visual system. The CSS rendering does not validate or normalize incoming data. If a business rule requires canonical casing, perform that rule in application code with a defined locale and retain the original where needed. Set the correct lang on translated text so the browser has a chance to use the right mapping. For a long translated state, let the badge grow rather than hiding characters with ellipsis.",
    '.review-state { text-transform: uppercase; letter-spacing: .04em; font-weight: 600; white-space: normal; }\n.person-name, .case-identifier { text-transform: none; letter-spacing: normal; }',
    "The CSS operation is cheap, but uppercase often takes more inline space and can change wrapping at narrow widths. Measure the longest localized phrase in the actual badge component. A letter-spacing value that looks calm in Latin text can be awkward in another script; scope it to reviewed locales or remove it. Text-transform is not secure normalization and must not participate in equality tests or signatures. The source phrase remains what users select and copy, although assistive technology may pronounce styling differently. Keep status meaning in text and do not use case alone as the only state cue.",
    ["Do not use visual uppercase as data normalization.", "Do not transform names or case-sensitive IDs for layout convenience.", "Do not assume one mapping or tracking value fits every language."],
    ["css/language-selector-typography", "css/readable-type", "css/colors-and-contrast", "html/language-and-direction"],
)

add(
    "box-decoration-break-fragments",
    "CSS box-decoration-break: control a highlight across wrapped lines",
    "Choose how a decorated inline fragment paints when a label wraps.",
    "Box-decoration-break determines whether a fragmented box is decorated as one continuous box or as separate fragments. Clone repeats background, border, and padding treatment at each fragment; slice paints the decoration as a continuous box that has been cut at the break. Support for this property still varies, and some browsers require a prefixed form.",
    "An incident index highlights a short evidence label that can wrap on a narrow card. A cloned decoration gives each line its own padded boundary, so the second line does not appear to be missing a left edge. Keep the underlying text in normal inline markup; the decoration is not the label itself. Begin with a readable background and text contrast that work even if clone is ignored. Then test wrapping at several container widths, selection, high zoom, printing, and a browser using the prefixed declaration. A long translated label may form three or four fragments, which can look too much like separate controls. If that happens, use a simpler underline or border on the whole card instead of forcing a pill around every line. Do not use CSS fragmentation to group different records semantically; source markup must preserve that relationship.",
    '.evidence-label { background: #dceef0; color: #153945; padding: .12em .38em; border-radius: .3em; -webkit-box-decoration-break: clone; box-decoration-break: clone; }',
    "Each fragment may paint its own background and rounded corners. On a handful of labels the rendering cost is minor, but many heavily shadowed, multi-line labels can add paint work. The larger cost is inconsistent appearance across browsers. Keep the unprefixed rule after the prefixed one and verify the target support matrix. A cloned background does not change hit targets or the semantic boundary of a link. If the label is interactive, its real anchor or button needs a visible focus state that remains clear around every wrapped line. Avoid hard-coded line breaks merely to manufacture a pleasing fragment shape; content width changes.",
    ["Do not rely on clone as the only way text remains readable.", "Do not mistake wrapped fragments for separate semantic items.", "Do not force manual breaks to fit one screenshot."],
    ["css/text-wrapping-and-truncation", "css/fragmentation-break-inside", "css/link-decoration-states", "html/inline-text-meaning"],
)

add(
    "modal-backdrop-boundary",
    "CSS ::backdrop: dim a modal without faking modality",
    "Style the browser's top-layer backdrop while leaving focus and dismissal to the dialog behavior.",
    "The ::backdrop pseudo-element represents the surface immediately behind an element in the top layer. A modal dialog shown with showModal() receives a backdrop. Styling it does not turn a nonmodal dialog or a regular div into a modal interaction.",
    "A review screen opens a confirmation dialog before a destructive case action. Give the modal a restrained opaque backdrop that separates the dialog from busy records, while keeping the dialog content readable. The sample targets only the intended dialog class. Verify the dialog is actually opened modally, traps interaction as the platform expects, has a clear title and close route, and returns focus to the invoking control when appropriate. Test the backdrop with another top-layer element, at high zoom, in forced colors, and with motion reduction. A dark overlay can conceal context but cannot explain the action: the dialog text must identify what will be changed. Avoid a transparent backdrop over sensitive-looking controls that encourages users to click through; underlying interaction behavior comes from the dialog API, not the color of the overlay. When the UI is nonmodal, do not make it look modal merely by painting a sheet.",
    '.case-confirmation::backdrop { background-color: rgb(12 30 42 / 72%); }\n@media (forced-colors: active) { .case-confirmation::backdrop { background-color: Canvas; } }',
    "A solid or translucent color is cheap to paint compared with a full-screen blur. Backdrop filters can increase compositing work, especially during animation, and are unnecessary for this task. Measure text contrast on the dialog itself as well as the backdrop's separation from the page. Forced-color systems may override the color, so the dialog needs its own border and clear heading. A top-layer backdrop is separate from the dialog element; styling the page body will not replace it. CSS does not implement focus return, Escape handling, or a destructive-action guard; those belong to the platform and application flow.",
    ["Do not expect ::backdrop to make an ordinary div modal.", "Do not hide the dialog's purpose behind a visual overlay.", "Do not rely on backdrop paint for focus management or dismissal."],
    ["css/backdrop-filter-legibility", "css/stacking-contexts", "css/dark-mode-and-forced-colors", "html/dialog-and-details"],
)

add(
    "popover-open-state",
    "CSS :popover-open: style only the visible popover state",
    "Separate a popover's base surface from its shown-state emphasis.",
    "The :popover-open pseudo-class matches a popover while it is showing. It is a state selector, not a command that opens the element. The HTML popover attribute and an invoker or application call determine when the popover is shown.",
    "A case filter menu should look like a compact floating surface only while open. Give the popover a conservative base border and background, then add a stronger shadow in the showing state. Keep the invoker a real button with a clear name and verify pointer, keyboard, touch, and dismissal behavior. The sample does not depend on a transition, so a browser that does not support advanced entry animation still presents the menu. Test nested scrolling, high zoom, a viewport edge, and another top-layer element. Do not use :popover-open as a substitute for a menu's selection state or for an accessible announcement of changed filters. An auto popover may light-dismiss; a manual popover behaves differently and needs an explicit close path. Make that distinction in HTML and behavior before choosing the visual style. If the menu needs persistent application state, CSS alone cannot supply it.",
    '.case-filter-popover[popover] { max-inline-size: min(22rem, calc(100vw - 2rem)); border: 1px solid #58707d; background: #fff; color: #173441; padding: 1rem; }\n.case-filter-popover:popover-open { box-shadow: 0 .8rem 2rem rgb(12 30 42 / 24%); }',
    "A modest shadow has a small paint cost, but repeated large blurred shadows and animated filters can become expensive. More important is placement: a beautifully styled surface can still cover its invoker or render off-screen. Test the actual positioning rule and consider the available anchor-positioning support and fallback. The browser manages popover visibility and top-layer ordering, while CSS controls presentation. Do not set display block on a hidden popover just to inspect it in a static mockup; that can misrepresent the state. Keep the popover's content readable and reachable when the enhancement selector is ignored.",
    ["Do not assume :popover-open opens the popover.", "Do not use a visual open state as an accessibility announcement.", "Do not confuse auto dismissal with manual popover behavior."],
    ["css/anchor-positioning-overlays", "css/stacking-contexts", "html/native-popover", "html/manual-popover"],
)

add(
    "background-attachment-local-scroll",
    "CSS background-attachment local: move decoration with scrolled content",
    "Keep a background tied to a scroll area's contents rather than its frame.",
    "Background-attachment controls what a background is fixed to while scrolling. The local value ties it to the element's contents, so the background moves as that element scrolls. Scroll attaches it to the element's box, while fixed anchors it to the viewport; those three states are easy to confuse in nested scrollers.",
    "An audit ledger contains a bounded scroll area with a subtle top-to-bottom tint that belongs to the list content. The tint should travel when an operator scrolls the ledger, while a visible border stays on the frame. Use local on that one scroller. Test with enough rows to overflow, keyboard scrolling, touch, a short list, and print output. If the design is really meant to keep a stationary texture behind rows, scroll may be the better value; observe the behavior before choosing. A fixed viewport background can behave differently or be costly on mobile browsers, so do not reach for fixed solely to make a desktop mockup look impressive. Keep text contrast independent of the gradient at every scroll position. The background is decoration, not a sign that a row was processed. Semantic record order and row status remain in HTML and application data.",
    '.audit-ledger { max-block-size: 29rem; overflow-y: auto; border: 1px solid #78919d; background-image: linear-gradient(#e7f2f4, #fff); background-attachment: local; }\n@media print { .audit-ledger { max-block-size: none; overflow: visible; background-image: none; } }',
    "The gradient is small compared with an image download, but scrolling can still cause background repaint. Test on a low-end target device if the area is large or contains many composited children. A local background that changes color across the scrollable content may lower contrast behind rows midway through the list. Use a solid fallback color or row surfaces where necessary. The rule has no effect on a non-scrolling element that is too short to overflow, which can hide a mistaken design assumption during review. Avoid using background position as a substitute for scroll progress or audit state; CSS painting cannot validate a record.",
    ["Do not confuse local attachment with viewport-fixed attachment.", "Do not test only a short list that never scrolls.", "Do not let a changing gradient reduce text contrast."],
    ["css/overflow-and-scroll", "css/background-gradients-and-shadows", "css/print-styles"],
)


assert len(specs) == 8
titles = {path: row["title"] for path, row in by_path.items()}
titles.update({item["path"]: item["title"] for item in specs})
titles[quiz_path] = "CSS type and overlay decisions quiz"


def links(paths):
    assert all(path in titles for path in paths), paths
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in paths
    ) + "</ul>"


hub = by_path[hub_path]
hub["data"]["modules"].append({
    "title": "Type, fragments, and top-layer surfaces",
    "summary": "Control font transfer, language-sensitive rendering, wrapped decoration, and open overlay paint.",
    "lessons": [item["path"] for item in specs],
})
hub["body"] += "<h2>Type, fragments, and top-layer surfaces</h2>" + links([item["path"] for item in specs])
hub["updated_at"] = stamp

for index, item in enumerate(specs):
    row = copy.deepcopy(by_path["css/selectors-and-cascade"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + item["path"])),
               path=item["path"], title=item["title"], summary=item["summary"],
               subject="css-reference", sort_order=24090 + index,
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
    "css/font-loading": ["css/unicode-range-font-subsets"],
    "css/readable-type": ["css/ligatures-in-identifiers", "css/text-transform-display-case"],
    "css/hyphenation-and-language": ["css/language-selector-typography"],
    "css/text-wrapping-and-truncation": ["css/box-decoration-break-fragments"],
    "css/stacking-contexts": ["css/modal-backdrop-boundary", "css/popover-open-state"],
    "css/backgrounds-and-decorative-images": ["css/background-attachment-local-scroll"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Further rendering decisions</h2>" + links(targets)
    row["data"].setdefault("related", []).extend(
        {"path": target, "title": titles[target]} for target in targets
    )
    row["updated_at"] = stamp

questions = [
    ("What does unicode-range avoid on a Latin-only route?", ["Fetching a face whose range has no used characters", "Creating font subsets automatically", "Checking the font license"], 0, "The files must be subsetted already; the descriptor controls whether a face is considered."),
    ("What happens when one used glyph falls in a face's range?", ["The entire referenced face file can be fetched", "Only that glyph is downloaded", "The HTML lang attribute changes"], 0, "The descriptor does not stream individual glyphs."),
    ("What does font-variant-ligatures none change?", ["Glyph substitution in rendering", "The copied identifier bytes", "The server record key"], 0, "The source string remains unchanged."),
    ("Where should ligature suppression be scoped?", ["Identifier and code surfaces that need literal inspection", "All multilingual prose", "Only invisible pseudo-elements"], 0, "A narrow selector avoids harming prose or script shaping."),
    ("What establishes content language for assistive technology?", ["Correct document language markup", "A :lang() CSS selector", "A font-family name"], 0, "CSS reacts to language state; it does not declare it."),
    ("What does text-transform uppercase leave unchanged?", ["The source or stored string", "Rendered letter shapes", "Visual label width"], 0, "The transformation is presentational."),
    ("What does box-decoration-break clone do?", ["Paint each fragment's decoration independently", "Remove wrapped text", "Prevent all line breaks"], 0, "Each wrapped fragment gets its own decoration treatment."),
    ("What must happen for a dialog to receive a modal backdrop?", ["It must be shown modally in the top layer", "It needs only a high z-index", "Its parent needs opacity"], 0, "Backdrop styling does not create modal behavior."),
    ("What does :popover-open represent?", ["A currently shown popover", "Any button that might open one", "A submitted filter value"], 0, "The selector matches the showing popover state."),
    ("What controls an auto popover's opening and dismissal?", ["HTML and browser behavior", "A box-shadow declaration", "A border-radius declaration"], 0, "CSS only styles the state."),
    ("What does background-attachment local follow?", ["The scroll area's content", "The viewport at all times", "The browser tab title"], 0, "Local moves the background with the element's scrollable contents."),
    ("Why test a background-attachment lesson with enough rows?", ["The values differ visibly only when content scrolls", "The gradient needs a network request", "A short list disables CSS parsing"], 0, "A non-overflowing list cannot demonstrate the scroll relationship."),
]
assert len(questions) == 12
quiz = copy.deepcopy(by_path["quizzes/css-advanced"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
            path=quiz_path, title=titles[quiz_path],
            summary="Twelve checks on font loading, language, wrapping, overlays, and scroll decoration.",
            sort_order=3109, status="published", published_at=stamp,
            created_at=stamp, updated_at=stamp)
quiz["data"] = {
    "subject_root": "css/css-tutorial", "section_path": "css/quizzes",
    "content_format": "html", "author_path": "authors/aitrove-editorial",
    "seo_ready": True, "duration_minutes": 12,
    "related": [{"path": target, "title": titles[target]} for target in [
        "css/unicode-range-font-subsets", "css/language-selector-typography",
        "css/modal-backdrop-boundary", "css/background-attachment-local-scroll"]],
    "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                       answer=(answer - index % 3) % 3, explanation=explanation)
                  for index, (prompt, options, answer, explanation) in enumerate(questions)],
}
quiz["body"] = (
    "<p>Check what CSS controls in typography, wrapped decoration, top-layer presentation, and scrolling backgrounds. Each question has one answer and an explanation.</p>"
    "<h2>Review the decisions</h2>" + links([item["path"] for item in quiz["data"]["related"]])
    + "<h2>Other checks</h2>" + links(["css/quizzes", "quizzes/css-scroll-state"])
    + "<h3>Common Mistakes</h3><ul><li>Do not treat presentation as stored data or platform behavior.</li>"
    "<li>Do not infer a network saving without inspecting real resource transfers.</li></ul>"
)
rows.append(quiz)
quiz_hub = by_path["css/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Type and overlay check</h2>" + links([quiz_path])
quiz_hub["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_quizzes": 1,
                  "total_records": len(rows)}))
