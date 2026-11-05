"""Add original prompt contracts for accessible output and a release exercise."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
lookup = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
subject_root = "prompt-engineering/prompt-engineering"
applications = "prompt-engineering/applications"
production = "prompt-engineering/production"
projects = "prompt-engineering/projects"
quizzes = "prompt-engineering/quizzes"
project_path = "prompt-engineering/accessible-transit-alert-project"
quiz_path = "quizzes/prompt-engineering-accessible-output"

specs = [
    {
        "slug": "purpose-bound-image-alternatives",
        "title": "Image alternatives: prompt for purpose, then check the image",
        "summary": "Distinguish decorative, informative, functional, and complex images before drafting alternative text.",
        "definition": "Alternative text describes an image's purpose in its page context, not every visible pixel. A prompt must receive the image, its nearby copy, the destination or action if the image is a control, and a declared role: decorative, informative, functional, or complex. The generator should return a proposed short alternative plus a reason and an uncertainty marker. A decorative image can receive an empty alternative in the rendered page. A complex chart needs its important relationships in nearby text or a data equivalent; a crowded one-sentence alternative cannot carry the entire analysis. No image evidence means no visual claim. A human editor chooses the role and checks the rendered result.",
        "case": "A fictional transit bulletin shows a small blue route icon beside the heading 'Line K diversion'. Because the heading already carries the route identity and the icon adds no information, the editor marks it decorative. A second graphic is a route map: Stops Alder and Birch are closed, and a shuttle serves Cedar. Its adjacent bulletin text omits Birch. The assistant drafts a short map alternative and a separate textual route sequence; the reviewer compares both against the approved map and corrects the missing stop before release. If the icon becomes a link to the route status page, its alternative must name that destination instead of the color or shape.",
        "sample": "INPUT: asset=MAP-47; context=Line K diversion; role=complex map.\nVerified features: Alder and Birch closed; shuttle at Cedar.\nOUTPUT: short_alt='Line K diversion map'; detail='Alder and Birch closed; shuttle boards at Cedar.'\nREVIEW: compare detail with approved map; publish both in page context.",
        "cost": "For I assets and an average of F verified features per asset, feature checking is O(IF) review work; generating a short sentence does not remove that work. Keep the approved feature list beside the asset version so a revised map invalidates its old description. A vision model may reduce drafting time, yet it can miss tiny labels or infer a nonexistent connection. If the map cannot be read with enough certainty, request the underlying route data. The site editor must verify the actual HTML alternative and the adjacent detail, not only the model's proposed string.",
        "mistakes": ["Do not describe a decorative icon as if it adds new information.", "Do not use a link image's appearance in place of its destination or action.", "Do not compress a complex map into a short alternative without a usable detail equivalent."],
        "related": ["prompt-engineering/image-region-verification-contract", "prompt-engineering/image-generation-brief-and-review", "html/html-tutorial/accessibility", "html/figure-and-caption"],
        "section": applications,
    },
    {
        "slug": "caption-transcript-evidence-contract",
        "title": "Caption and transcript prompts: keep timing, speakers, and sound evidence",
        "summary": "Separate synchronized captions from a readable transcript and verify both against media.",
        "definition": "Captions are synchronized text for speech and meaningful non-speech audio; a transcript is a text document that can also describe relevant visual information. Prompt them as separate artifacts. Give the assistant a time-aligned speech record, speaker labels where known, a list of meaningful sounds, visual facts needed to understand the clip, and uncertainty intervals. It may propose caption cues and transcript paragraphs. It must not fill an inaudible word merely to make the sentence smooth. A reviewer checks timing on the actual player, identifies overlapping speakers, and verifies the transcript's visual details against frames. Translation is another pass with its own reviewer; it cannot repair an incorrect source transcript.",
        "case": "A 74-second Line K alert contains a dispatcher saying, 'Board at Cedar', while a second voice begins over the word 'Cedar'. The source transcript marks the overlap at 00:39 and leaves a two-word interval uncertain. The assistant initially assigns both lines to the dispatcher and omits an audible warning chime. The media reviewer replays that interval, separates the voices, records the chime because it signals a service alert, and leaves the unresolved words marked for review. The public transcript also describes the on-screen diversion diagram; the captions remain short, timed cues for the player.",
        "sample": "00:37.200 dispatcher: Board at Cedar.\n00:39.100 second speaker: [overlap; words unclear]\n00:41.500 [service alert chime]\nCaption gate: speakers, sound, timing checked against media.\nTranscript gate: include verified visual diversion detail.",
        "cost": "Reviewing media duration D at ordinary playback speed takes at least O(D) wall time, and difficult overlaps can require several passes. With C caption cues, a cue-by-cue timing check is O(C) after the media is understood. Store the media hash, transcript version, cue times, and review decisions so a re-edit does not silently reuse stale captions. A model draft saves typing but cannot establish that all audio was audible or every frame was inspected. Sample audits are useful for routine changes; a changed spoken warning needs full review of the affected segment and neighboring cues.",
        "mistakes": ["Do not convert uncertain audio into confident words.", "Do not treat a plain transcript as synchronized captions.", "Do not omit meaningful sounds or visual facts needed to understand the clip."],
        "related": ["prompt-engineering/audio-overlap-speaker-review", "prompt-engineering/audio-transcription-uncertainty", "prompt-engineering/video-timecode-evidence", "html/video-captions"],
        "section": applications,
    },
    {
        "slug": "semantic-structure-output-gate",
        "title": "Semantic output prompts: verify structure after generation",
        "summary": "Require actual headings, lists, and table relationships instead of visual lookalikes.",
        "definition": "A prompt can ask for a heading outline and meaningful lists, but semantic structure exists in the rendered document. The generation contract should specify the content hierarchy, allowed elements, and fields that must keep their relationships. A heading styled with bold text is not a heading; a row of spaces is not a data table. For an operational notice, request a concise heading, paragraphs for context, a list for route changes, and a structured data source for a schedule. The renderer, not the model, owns final markup. Inspect its document tree and keyboard order. If the publishing surface cannot express required table headers or media alternatives, change the template or attach a suitable equivalent before release.",
        "case": "The Line K assistant produces a timetable as columns padded with spaces. It looks aligned in a desktop preview, but its stop and time values lose their relationship when read linearly. The editor instead sends typed stop and departure records to the site renderer, which builds row and column headers. The assistant drafts a heading outline and a short route-change list. A reviewer checks that the bulletin has one clear topic heading, that nested sections match the content, and that a keyboard user reaches the schedule after the disruption summary rather than through an unrelated control.",
        "sample": "Content contract: title; diversion summary; affected stops list; schedule rows.\nTyped row: stop=Cedar; departure=08:47; service=shuttle.\nRenderer: heading hierarchy + real list + header-associated schedule.\nGate: inspect document tree and keyboard reading order.",
        "cost": "For N content nodes, a structural tree walk is O(N) time and O(H) stack space for nesting depth H; checking human meaning still requires editorial review. Typed schedule rows prevent the model from inventing spacing as a presentation format. Automated checks can detect missing heading elements or header associations, but they cannot decide whether 'Service update' is descriptive enough for this particular page. Keep a small template test with empty, one-row, and long schedules. Recheck the rendered page after CSS changes because visual order and reading order can drift apart.",
        "mistakes": ["Do not call bold text a semantic heading.", "Do not serialize a schedule as space-padded prose.", "Do not assume the prompt alone determines the final document tree."],
        "related": ["prompt-engineering/output-sink-validation", "html/headings-and-paragraphs", "html/data-tables", "html/complex-table-headers"],
        "section": applications,
    },
    {
        "slug": "plain-language-link-and-qualification-review",
        "title": "Plain-language prompts: simplify without losing conditions",
        "summary": "Make notices easier to scan while retaining eligibility, times, and useful link names.",
        "definition": "A plain-language rewrite should reduce unnecessary phrasing while preserving every operational condition. Supply the source facts as a structured list: who is affected, what changes, when it starts and ends, what remains uncertain, and where the reader can act. Require the draft to map each output sentence back to one or more facts. Ask for link text that names the destination or action without relying on nearby words such as 'here'. The assistant may split a long sentence or explain a technical term, but it must not turn 'eligible riders may claim' into 'all riders receive'. Compare dates, thresholds, and negations mechanically where possible, then have an editor judge whether the result reads plainly to its audience.",
        "case": "A transit refund notice says that riders who paid before 08:30 and could not use Line K between 08:45 and 10:15 may file a claim within 47 days. The first AI draft says, 'All Line K riders get a refund today' and offers a link named 'Learn more'. Both are wrong: eligibility widened, filing became payment, and the link hides its purpose. The corrected notice states the affected window and filing deadline, labels the link 'File a Line K disruption claim', and keeps the claim decision separate from the notice. Reviewers compare the draft with the approved eligibility record, including the exact time zone.",
        "sample": "FACT: paid_before=08:30; disruption=08:45–10:15; file_within=47 days.\nDRAFT: eligible riders may file a claim; decision follows review.\nLINK: File a Line K disruption claim.\nREJECT: all riders get a refund today; Learn more.",
        "cost": "With F source facts and S draft sentences, a recorded fact-to-sentence map costs O(F+S) to store and O(FS) in a naive full comparison. A keyed field check reduces date and threshold review, but meaning and clarity still need a person. Keep the approved facts in structured form so a changed filing window can mark old prose stale. Readability scores cannot detect a reversed condition. A shorter notice is useful only when the reader retains the right action and the limits on that action.",
        "mistakes": ["Do not widen eligibility while shortening a sentence.", "Do not replace a filing opportunity with a guaranteed payment.", "Do not use vague link text when the destination can be named."],
        "related": ["prompt-engineering/evidence-bound-report-summary", "prompt-engineering/multilingual-equivalence-check", "html/html-tutorial/accessibility", "prompt-engineering/template-variable-escaping"],
        "section": applications,
    },
    {
        "slug": "accessible-output-evaluation-slices",
        "title": "Accessible output evaluations: measure failures by artifact and user task",
        "summary": "Pair automated contract checks with media, keyboard, and assistive-technology review.",
        "definition": "An accessible-output evaluation must state the user task and the artifact being tested. A single pass/fail label hides whether the defect is a hallucinated map detail, a missing caption cue, a broken heading order, or a misleading claim link. Build slices for decorative and complex images, overlapped audio, short and long schedules, plain-language conditions, and translated notices. Record expected facts, permissible uncertainty, generated artifact, rendered artifact, and reviewer decision. Automated assertions should check structural invariants and data equality. Human reviewers must inspect the actual image or media and perform representative keyboard and assistive-technology tasks on the rendered page. Treat model confidence as an annotation, never as a substitute for evidence.",
        "case": "The Line K release has 31 fixtures: 6 image roles, 7 caption intervals, 8 schedule shapes, 5 eligibility notices, and 5 localized variants. A model revision fixes an omitted chime yet changes a map description to say the shuttle boards at Birch. The caption slice improves, while the image slice fails. Promotion stays blocked. The reviewer stores the map asset version, failed feature ID, renderer build, and affected page route. A separate keyboard check confirms the claim link can be reached and its name conveys the destination without needing the previous sentence. The team repairs the map draft and reruns only impacted fixtures plus a small full-set regression.",
        "sample": "Fixture MAP-47: shuttle boarding=Cedar; generated claim=Birch -> fail.\nFixture AUDIO-12: chime at 00:41.500; cue present -> pass.\nFixture LINK-08: accessible name='File a Line K disruption claim' -> review.\nRelease gate: no critical unsupported facts; rendered task check complete.",
        "cost": "For A artifacts, V prompt variants, and R review modes, exhaustive evaluation takes O(AVR) checks; media review adds duration-dependent time. Use risk-based regression selection after small edits, but keep the whole critical task set for promotion. Structural checks are cheap and repeatable; assistive-technology sessions cost more and may expose defects those checks miss. Track failures by artifact, impact, and owner instead of averaging them into one accessibility score. A passing prompt fixture does not prove the published renderer, player, or CMS template produces the same result.",
        "mistakes": ["Do not average a false route instruction away with many clean captions.", "Do not stop at model output without checking the rendered page.", "Do not use automated checks as proof that a human task is usable."],
        "related": ["prompt-engineering/evaluation-slice-design", "prompt-engineering/negative-control-prompt-evaluation", "prompt-engineering/video-frame-sampling-disclosure", "html/html-tutorial/accessibility"],
        "section": production,
    },
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]).intersection(lookup)
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: release an accessible transit disruption alert"
titles[quiz_path] = "Accessible prompt output decisions"


def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(selected):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(selected)) + "</ul>"


def related(selected):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(selected)]


def article(path, title, summary, body, section, order, connections, kind="tutorial"):
    entry = copy.deepcopy(lookup["prompt-engineering/evaluation-slice-design"])
    subject = "prompt-engineering-applications" if section == applications else "prompt-engineering-production" if section == production else "prompt-engineering-project"
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)),
                 path=path, title=title, summary=summary, body=body,
                 subject=subject, difficulty="Advanced", tags=["prompt engineering", "accessible output"],
                 sort_order=28800 + order, status="published", published_at=stamp,
                 created_at=stamp, updated_at=stamp)
    entry["data"].update(kind=kind, reading_minutes=11 if kind == "tutorial" else 19,
                         author_path="authors/aitrove-editorial", subject_root=subject_root,
                         section_path=section, content_format="html", seo_ready=True,
                         related=related(connections))
    return entry


new_rows = []
for index, (path, spec) in enumerate(zip(paths, specs)):
    connections = [spec["section"], subject_root] + spec["related"] + [peer for peer in paths if peer != path] + [project_path, quiz_path]
    body = ("<p>" + html.escape(spec["definition"]) + "</p>"
            + "<h2>Operational case</h2><p>" + html.escape(spec["case"]) + "</p>"
            + f'<pre><code class="language-text">' + html.escape(spec["sample"], quote=False) + "</code></pre>"
            + "<h2>Performance and operating cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
            + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(mistake) + "</li>" for mistake in spec["mistakes"]) + "</ul>"
            + "<h2>Connected lessons</h2>" + links(connections))
    new_rows.append(article(path, spec["title"], spec["summary"], body, spec["section"], index * 10, connections))

project_connections = paths + ["prompt-engineering/image-region-verification-contract", "prompt-engineering/audio-overlap-speaker-review", "prompt-engineering/multilingual-equivalence-check", "html/complex-table-headers", quiz_path]
project_body = (
    "<p>A fictional transit agency must publish a Line K disruption alert. Its release packet contains a diversion map, a 74-second spoken update, a stop schedule, a claim notice, and two localized versions. Build a prompt contract and review path for each artifact. Keep approved service facts as typed records: Alder and Birch are closed; the shuttle boards at Cedar; the claim applies only to riders meeting the payment and disruption windows. No assistant output becomes public until its claims and final rendering are checked.</p>"
    "<h2>Prepare the artifacts</h2><p>Classify the route icon as decorative in the heading context, then create a short map alternative and nearby route detail from the approved map. Draft timed captions from the recording, preserving the overlap at 00:39 and the service chime at 00:41.500. Produce a transcript that also explains the on-screen diversion diagram. Send stop and departure rows to a renderer that creates real table headers rather than asking the model for aligned spaces. Rewrite the claim notice in plain language without widening eligibility or promising immediate payment.</p>"
    "<h2>Check the published task</h2><p>Test a reader trying to find the shuttle stop, hear or read the alert, inspect the next departure, and file a valid claim. Include one control with an unreadable map label and another with an unknown spoken phrase; the model must mark uncertainty instead of inventing facts. Compare the localized notices with the same eligibility record. Inspect the rendered page with keyboard and assistive technology as well as structural checks. Record the image version, media hash, renderer build, reviewer, failures, and release decision. A false boarding stop blocks release even when every other fixture passes.</p>"
    '<pre><code class="language-text">Map: Alder/Birch closed; board shuttle at Cedar.\nAudio: overlap 00:39; chime 00:41.500; unresolved words stay marked.\nSchedule row: Cedar | 08:47 | shuttle; renderer owns headers.\nClaim: paid before 08:30; affected 08:45–10:15; file within 47 days.\nGate: verified facts + rendered task check; false stop -> block.</code></pre>'
    "<h2>Performance and operating cost</h2><p>Let A be artifact fixtures, V prompt variants, and R review modes. The broad evaluation is O(AVR), plus O(D) playback time for total media duration D and a structural walk linear in document nodes. Reuse typed facts and approved versions across drafts; this prevents a map revision from leaving stale prose behind. Keep separate defect counts for unsupported visual facts, caption omissions, structure, misleading claim conditions, and locale drift. Human playback and task review are slower than a schema check, but a schema check cannot hear an overlapped warning or judge whether the page makes the shuttle stop findable.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not publish a model's map description without comparing it to the approved asset.</li><li>Do not confuse a transcript with synchronized captions.</li><li>Do not infer accessibility from a passing prompt test when the published template has not been inspected.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Verify image, audio, structure, plain language, and rendered access for one transit alert.", project_body, projects, 60, project_connections, kind="project"))

questions = [
    ("A route icon repeats the adjacent route heading and adds no information. What role fits?", "Decorative, with an empty rendered alternative", "A complete description of its colors", "A fabricated route direction", "The nearby heading already carries its meaning."),
    ("The same icon becomes the only link to status. What should its alternative convey?", "The link destination or action", "Only its color", "Nothing, because it was once decorative", "A control needs an accessible purpose in its current context."),
    ("A complex map contains closed stops. Where should full route detail live?", "In nearby usable text or a data equivalent", "Only in a crowded short alternative", "Only in the file name", "A short alternative cannot carry every relationship."),
    ("Two speakers overlap and a phrase is unclear. What should the transcript do?", "Mark the interval uncertain and review it", "Invent a fluent sentence", "Delete both speakers", "Uncertainty should remain visible until checked."),
    ("A timed player needs text for an alert chime. Which artifact carries it?", "Synchronized caption cues", "Only the page title", "Only a decorative image alternative", "Meaningful sound belongs in captions for the timed media."),
    ("The video adds a diversion diagram with facts absent from speech. What can cover it in text?", "A verified descriptive transcript", "An unrelated subtitle", "A claim that the visual is obvious", "Visual information needs an equivalent path."),
    ("A model pads schedule columns with spaces. What should happen?", "Render typed rows with associated headers", "Publish the spaces as a table", "Use bold text for every cell", "Visual alignment is not a structural relationship."),
    ("A generated notice uses bold text as a section title. What must be checked?", "The rendered heading hierarchy", "Only its font size", "Only the prompt wording", "Semantic structure is present in the document tree."),
    ("A rewrite turns eligible claimants into all riders. What failed?", "The eligibility condition was changed", "The sentence became shorter", "The link moved below the text", "Plain language must retain conditions."),
    ("Which link label best names the claim destination?", "File a Line K disruption claim", "Click here", "More", "The destination should make sense on its own."),
    ("All captions pass but the map names the wrong shuttle stop. Release?", "Block and repair the unsupported map fact", "Average the scores", "Publish because captions passed", "A critical false instruction is not canceled by other passes."),
    ("The prompt output passes structural checks. What remains?", "Inspect the rendered task with keyboard and assistive technology", "Assume the CMS preserved all semantics", "Skip media review", "The published surface can differ from the model draft."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-multimodal-evidence"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                  path=quiz_path, title=titles[quiz_path],
                  summary="Test alternatives, captions, structure, claim wording, and release gates.",
                  body="<p>Choose the decision that preserves the user task. A convincing draft still needs evidence and a rendered-page check.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, production, quizzes]),
                  sort_order=28870, status="published", published_at=stamp,
                  created_at=stamp, updated_at=stamp)
quiz_entry["data"].update(subject_root=subject_root, section_path=quizzes,
                          content_format="html", author_path="authors/aitrove-editorial",
                          seo_ready=True, duration_minutes=12,
                          related=related(paths + [project_path]),
                          questions=[{"prompt": prompt,
                                      "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                      "answer": (-index) % 3, "explanation": explanation}
                                     for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)])
new_rows.append(quiz_entry)

for hub_path, selected, title, summary in [
    (applications, paths[:4], "Accessible output contracts", "Draft image alternatives, captions, semantic structure, and plain-language notices from verified facts."),
    (production, paths[4:], "Accessible output evaluation", "Check artifact failures and rendered user tasks before promotion."),
    (projects, [project_path], "Accessible transit alert", "Release one disruption notice across image, media, schedule, and claim surfaces."),
    (quizzes, [quiz_path], "Accessible output decisions", "Test image, media, structure, wording, and release boundaries."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

root_hub = lookup[subject_root]
root_hub["body"] += "<h2>Accessible prompt outputs</h2><p>Keep generated descriptions, timed text, page structure, and claims tied to evidence and rendered tasks.</p>" + links(paths + [project_path, quiz_path])
root_hub["updated_at"] = stamp

backlinks = {
    "prompt-engineering/image-region-verification-contract": paths[0],
    "prompt-engineering/audio-overlap-speaker-review": paths[1],
    "prompt-engineering/output-sink-validation": paths[2],
    "prompt-engineering/evidence-bound-report-summary": paths[3],
    "prompt-engineering/evaluation-slice-design": paths[4],
    "html/html-tutorial/accessibility": paths[2],
    "html/video-captions": paths[1],
    "html/complex-table-headers": paths[2],
}
for old_path, new_path in backlinks.items():
    entry = lookup[old_path]
    entry["body"] += "<p><strong>Continue with:</strong> " + link(new_path) + ".</p>"
    entry["data"]["related"] = related([item["path"] for item in entry["data"].get("related", [])] + [new_path])
    entry["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newLessons": len(specs), "newProjects": 1, "newQuizzes": 1,
                  "newPaths": [entry["path"] for entry in new_rows]}))
