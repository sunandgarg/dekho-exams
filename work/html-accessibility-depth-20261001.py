"""Add distinct HTML accessibility and input lessons to the preview curriculum."""

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
lessons = []


def add(slug, section, title, definition, case, sample, boundary, cost, mistakes, links):
    lessons.append((slug, section, title, definition, case, sample, boundary, cost, mistakes, links))


add("table-caption-and-summary", "accessibility", "HTML table caption and summary: explain a dense data grid",
    "A table caption names the table; nearby summary text can explain a complex row or column structure before a reader enters the cells.",
    "An operations report lists failed seal checks by depot and shift. The short caption tells a reader which table this is. A visible paragraph explains that each depot has two shifts and that the final column counts unresolved checks. Those are different jobs. A screen-reader user can identify the table from its caption, while anyone can read the structural note before working through the numbers. Header cells still need correct scope or explicit associations; a summary does not repair a broken header graph.",
    '''<p id="seal-grid-guide">Each depot has a morning and evening row. The last column counts checks still open.</p>
<table aria-describedby="seal-grid-guide">
  <caption>Seal checks by depot and shift</caption>
  <thead><tr><th scope="col">Depot</th><th scope="col">Shift</th><th scope="col">Open checks</th></tr></thead>
  <tbody>
    <tr><th scope="row">North</th><td>Morning</td><td>4</td></tr>
    <tr><th scope="row">North</th><td>Evening</td><td>2</td></tr>
    <tr><th scope="row">West</th><td>Morning</td><td>7</td></tr>
    <tr><th scope="row">West</th><td>Evening</td><td>1</td></tr>
  </tbody>
</table>''',
    "The description points to a visible paragraph rather than hiding instructions in an obsolete table summary attribute. Do not add a long summary to a simple grid that is already clear from its caption and headers.",
    "Caption and description add a small amount of markup and editorial work. The heavier cost comes from maintaining accurate header associations as columns change; test a dense table with keyboard and screen-reader table navigation.",
    ["Do not repeat the caption in the summary.", "Do not use the caption as a substitute for row and column headers.", "Do not force unrelated layout content into a data table."],
    ["html/data-tables", "html/complex-table-headers", "html/table-column-groups"])

add("video-descriptive-transcript", "media", "HTML video transcript: retain information beyond timed captions",
    "A video transcript is a readable text alternative; a descriptive transcript also records visual information needed to understand the video.",
    "A safety clip shows how an inspector notices a split seal. The caption track covers speech and meaningful sounds at the right times, while the transcript lets a reader scan the procedure without playing the clip and includes the visual action that the narrator never says aloud. Keep the transcript adjacent to the video and written in the same language as the clip. If the clip changes, update both timed captions and transcript; a stale transcript can describe the wrong procedure and create a safety error.",
    '''<section aria-labelledby="seal-video-title">
  <h2 id="seal-video-title">Inspecting a split parcel seal</h2>
  <video controls preload="metadata" width="720" height="405">
    <source src="/media/split-seal-I-47.webm" type="video/webm">
    <track kind="captions" src="/media/split-seal-I-47.en.vtt" srclang="en" label="English captions" default>
    <p>The inspection video is unavailable in this browser.</p>
  </video>
  <h3>Descriptive transcript</h3>
  <p>Inspector: “Check the upper seam before release.” A hand turns parcel I-47; the red seal has a visible split above the code. The inspector records the split and moves the parcel to the hold shelf.</p>
</section>''',
    "Captions and transcripts serve different reading patterns. The text shown here is a short illustrative excerpt; a real transcript must cover the entire clip, including meaningful speech, sounds, and visual actions. Media and caption routes must exist before publication.",
    "A transcript adds editorial and revision cost but little runtime cost. It is searchable and usable without video playback, while the media files and caption track still dominate delivery bytes.",
    ["Do not publish an excerpt as though it were a full transcript.", "Do not treat a caption file as a description of unspoken visual action.", "Do not let the transcript diverge when the video is re-edited."],
    ["html/video-captions", "html/video-track-languages", "html/video-source-fallback"])

add("audio-transcript", "media", "HTML audio transcript: make a recording readable without playback",
    "An audio transcript expresses the meaningful speech and non-speech audio of a recording as text.",
    "A depot dispatch recording contains a spoken route change and an alarm that explains why the route changed. A useful transcript identifies speakers and the alarm instead of writing only a loose summary of the decision. The audio player remains available for people who want timing, tone, or verification. The transcript sits beside it, so searching and copying a route instruction does not require scrubbing through the recording. If privacy rules restrict the recording, apply the same access policy to the transcript.",
    '''<section aria-labelledby="dispatch-audio-title">
  <h2 id="dispatch-audio-title">Depot west dispatch update</h2>
  <audio controls preload="none">
    <source src="/media/dispatch-west-47.ogg" type="audio/ogg">
    <p>The dispatch recording is unavailable in this browser.</p>
  </audio>
  <h3>Transcript</h3>
  <p>Dispatcher: “Use gate four for the 16:40 departure.” Alarm sounds. Dispatcher: “Gate two is closed until the sensor check is complete.”</p>
</section>''',
    "The sample transcript is a complete miniature recording only if the media contains exactly those statements and sound. In a real publication workflow, compare the text against the final audio and provide any required speaker or sound context.",
    "Text is cheap to deliver, but accurate transcription and review take time. Preload=none avoids an eager media request in many browsers; it is only a hint and does not replace bandwidth testing.",
    ["Do not publish a summary in place of a transcript when exact instructions matter.", "Do not omit meaningful non-speech sounds.", "Do not expose a restricted recording's contents through a public transcript."],
    ["html/audio-controls", "html/video-descriptive-transcript", "html/sections-and-articles"])

add("telephone-input", "forms", "HTML telephone input: preserve symbols and validate your own format",
    "An input with type=tel identifies a telephone number field without imposing one universal phone-number syntax.",
    "A depot contact field accepts international numbers. A number input would be the wrong model: phone numbers can contain a leading plus sign, spaces, extensions, and leading zeroes that are identifiers rather than quantities. The visible help asks for a country code and explains the intended format, while autocomplete tells the browser the field's purpose. The application must normalize only according to a documented policy, validate the number for the supported regions, and confirm consent before using it for calls or messages.",
    '''<form action="/depots/west/contact" method="post">
  <label for="dispatch-phone">Dispatch telephone number</label>
  <p id="phone-help">Include the country code, such as +44 20 7946 0472.</p>
  <input id="dispatch-phone" name="telephone" type="tel" autocomplete="tel" aria-describedby="phone-help" required>
  <button type="submit">Review contact change</button>
</form>''',
    "Type=tel can influence mobile keyboard layout but does not guarantee a valid number or a callable endpoint. A copied number and a malicious request can bypass every client-side hint.",
    "The native field adds no script bundle. Region-aware parsing, persistence, and consent handling are the real costs; careless numeric conversion can permanently remove a leading zero or plus sign.",
    ["Do not use type=number for telephone identifiers.", "Do not assume every region shares one length or prefix rule.", "Do not contact a number solely because a browser accepted it."],
    ["html/number-input-or-text", "html/autocomplete-and-inputmode", "html/form-help-and-errors"])

add("image-submit-button", "forms", "HTML image submit button: supply an action name and handle coordinates carefully",
    "An input with type=image is a submit control whose alt text names the action; a pointer activation can also submit coordinates within the image.",
    "A legacy warehouse map allows selecting a zone by clicking a diagram. Its image submit button sends a location coordinate, but keyboard users may activate the same control without a meaningful point. The server therefore offers a text list of zones and never makes coordinate data the only path to a decision. If an image merely decorates an ordinary submit action, use a regular button with text instead. The alt text here names the result of activating the control rather than describing the pixels.",
    '''<form action="/warehouse/zones/choose" method="get">
  <p>Select a zone from the map or use the list.</p>
  <input type="image" name="zone_point" src="/images/warehouse-zones.webp" alt="Choose a warehouse zone from the map" width="520" height="360">
  <label for="zone-list">Zone list</label>
  <select id="zone-list" name="zone">
    <option value="">Choose from the list</option>
    <option value="north-dock">North dock</option>
    <option value="returns-bay">Returns bay</option>
  </select>
  <button type="submit">Choose listed zone</button>
</form>''',
    "The map and list are alternatives, not two independent decisions. The server must reject ambiguous submissions, map coordinates to a current zone layout, and authorize access. A keyboard activation may not supply a useful location, so the list must remain functional.",
    "A map image adds bytes and maintenance when zones move. The coordinate conversion and fallback path cost more than the control itself; for many tasks, a labelled list is simpler and less error-prone.",
    ["Do not leave an image button without meaningful alt text.", "Do not require a precise pointer coordinate as the sole selection method.", "Do not trust submitted coordinates without bounds and zone checks."],
    ["html/image-maps", "html/linked-image-alt", "html/select-and-textarea"])


new_paths = {"html/" + lesson[0] for lesson in lessons}
assert len(lessons) == 5 and not new_paths.intersection(by_path)
assert all(set(lesson[-1]) <= set(by_path) | new_paths for lesson in lessons)
titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"html/" + lesson[0]: lesson[2] for lesson in lessons})


def body_for(lesson):
    _, _, _, definition, case, sample, boundary, cost, mistakes, links = lesson
    return (
        "<p>" + html.escape(definition) + "</p>"
        "<h2>Use case</h2><p>" + html.escape(case) + "</p>"
        '<pre><code class="language-html">' + html.escape(sample, quote=False) + "</code></pre>"
        "<h2>Behavioral boundary</h2><p>" + html.escape(boundary) + "</p>"
        "<h2>Cost and maintenance</h2><p>" + html.escape(cost) + "</p>"
        "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in mistakes) + "</ul>"
        "<h2>Connected lessons</h2><ul>" + "".join(
            '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in links
        ) + "</ul>"
    )


by_section = {}
for index, lesson in enumerate(lessons):
    slug, section, title, definition, _, _, _, _, _, links = lesson
    path = "html/" + slug
    hub_path = "html/html-tutorial/" + section
    hub = by_path[hub_path]
    row = copy.deepcopy(by_path["html/document-skeleton"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), path=path,
               title=title, summary=definition, body=body_for(lesson), subject=hub["subject"],
               tags=["html", section], sort_order=2400 + index,
               created_at=stamp, updated_at=stamp, published_at=stamp)
    row["data"] = {"subject_root": "html/html-tutorial", "section_path": hub_path,
                   "content_format": "html", "kind": "tutorial", "reading_minutes": 7,
                   "author_path": "authors/aitrove-editorial", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in links]}
    rows.append(row)
    by_path[path] = row
    by_section.setdefault(section, []).append(path)

for section, paths in by_section.items():
    hub = by_path["html/html-tutorial/" + section]
    hub["data"]["modules"].append({"title": "Readable data and input contracts",
                                    "summary": "Accessible tables, media alternatives, and honest form behavior.",
                                    "lessons": paths})
    additions = "<h2>Readable data and input</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in paths
    ) + "</ul>"
    hub["body"] = hub["body"].replace("<h3>Common Mistakes</h3>", additions + "<h3>Common Mistakes</h3>", 1)
    hub["updated_at"] = stamp

for lesson in lessons:
    path = "html/" + lesson[0]
    target = by_path[lesson[-1][0]]
    link = '<p><a href="/' + path + '">Related: ' + html.escape(titles[path]) + "</a>.</p>"
    if link not in target["body"]:
        target["body"] += link
        target["data"].setdefault("related", []).append({"path": path, "title": titles[path]})
        target["updated_at"] = stamp

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "articles")
