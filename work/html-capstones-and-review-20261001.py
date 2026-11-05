"""Connect the HTML projects and add two capstones with a focused review quiz."""

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


def linked(paths):
    return "".join(
        '<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>"
        for path in paths
    )


projects = [
    {
        "path": "html/incident-evidence-project",
        "title": "HTML incident evidence project: keep a record readable when video fails",
        "summary": "Build a read-only incident page with a data table, captioned clip, and descriptive transcript.",
        "body": (
            "<p>A read-only evidence page should explain the case before optional media loads. Its table needs a caption and real headers; its video needs captions and a text account of important visual action.</p>"
            "<h2>Build the record</h2><p>Use case C-47 as a bounded exercise. The first screen identifies the record and shows three evidence events in order. A reader can review the table without playback. The clip adds inspection detail; the transcript records spoken instructions, a warning tone, and the split seal visible in the frame. If a future edit changes the clip, revise its captions and transcript together. This project is about document structure, not a working evidence store or an authenticated case system.</p>"
            '<pre><code class="language-html">' + html.escape('''<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Case C-47 evidence record</title></head>
<body>
<main>
  <h1>Case C-47 evidence record</h1>
  <p>Parcel held after the upper seal split was found at intake.</p>
  <table>
    <caption>Evidence recorded for case C-47</caption>
    <thead><tr><th scope="col">Time</th><th scope="col">Event</th><th scope="col">State</th></tr></thead>
    <tbody>
      <tr><td>08:14</td><th scope="row">Seal check</th><td>Split found</td></tr>
      <tr><td>08:19</td><th scope="row">Photograph</th><td>Stored for review</td></tr>
      <tr><td>08:27</td><th scope="row">Dispatch hold</th><td>Open</td></tr>
    </tbody>
  </table>
  <h2>Seal inspection clip</h2>
  <video controls preload="metadata" width="720" height="405">
    <source src="/media/C-47-seal.webm" type="video/webm">
    <track kind="captions" src="/media/C-47-seal.en.vtt" srclang="en" label="English captions" default>
    <p>The clip is unavailable. Read the transcript below.</p>
  </video>
  <h3>Descriptive transcript</h3>
  <p>Inspector: “Stop dispatch.” A warning tone sounds. The upper seam is split above the parcel code; the inspector places the parcel on the hold shelf.</p>
</main>
</body></html>''', quote=False) + "</code></pre>"
            "<h2>Behavior and cost</h2><p>The clip and caption file are illustrative local paths; this static lesson does not ship them. A real case page needs an authorized route, real media, and review of the entire final transcript. The table costs little to render. Video bytes, storage, and revision work dominate. Test at narrow widths and without video loading: the record should still say what happened. Do not treat the table's state words as an auditable history unless the backend supplies immutable event data.</p>"
            "<h3>Common Mistakes</h3><ul><li>Do not make the video the only source of a decision-critical fact.</li><li>Do not publish a transcript excerpt as the full account of a longer clip.</li><li>Do not present fictional case data as a live record.</li></ul>"
            "<h2>Connected lessons</h2><ul>" + linked(["html/table-caption-and-summary", "html/video-descriptive-transcript", "html/video-captions", "html/data-tables"]) + "</ul>"
        ),
        "related": ["html/table-caption-and-summary", "html/video-descriptive-transcript", "html/video-captions", "html/data-tables"],
    },
    {
        "path": "html/server-error-response-project",
        "title": "HTML form error project: return values, summary links, and field repairs",
        "summary": "Model a server-rendered failed submission with preserved input and linked repair instructions.",
        "body": (
            "<p>A failed form submission needs a page-level result and field-level repair instructions. Return the person's entered values, mark only failed controls invalid, and connect each message to its control.</p>"
            "<h2>Render a useful failure</h2><p>Assume a server rejected inspection I-47 because the seal code was too short and the finding was empty. The response title and main heading announce two errors. Each summary link jumps to a control; the adjacent message states what to change. The code keeps the attempted seal value so a reviewer can correct it instead of starting over. This is the HTML for an error response, not a backend implementation. A real endpoint must validate and authorize every request, escape returned values, protect the POST, and preserve only data the reviewer is allowed to see.</p>"
            '<pre><code class="language-html">' + html.escape('''<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>2 errors — inspection I-47</title></head>
<body>
<main>
  <h1>Correct 2 fields in inspection I-47</h1>
  <nav aria-label="Form errors">
    <ul>
      <li><a href="#seal-code">Seal code: use two letters and four digits.</a></li>
      <li><a href="#inspection-finding">Finding: describe the observed condition.</a></li>
    </ul>
  </nav>
  <form action="/inspections/I-47/review" method="post">
    <label for="seal-code">Seal code</label>
    <input id="seal-code" name="seal_code" value="47" pattern="[A-Z]{2}[0-9]{4}" aria-invalid="true" aria-describedby="seal-code-error" required>
    <p id="seal-code-error">Enter a code such as SC0047.</p>
    <label for="inspection-finding">Finding</label>
    <textarea id="inspection-finding" name="finding" aria-invalid="true" aria-describedby="finding-error" required></textarea>
    <p id="finding-error">Describe the seal condition before review.</p>
    <button type="submit">Review inspection</button>
  </form>
</main>
</body></html>''', quote=False) + "</code></pre>"
            "<h2>Behavior and cost</h2><p>A full-page server response can use its title and heading to announce failure. If the same errors are injected into an already open page without navigation, an appropriate status or alert announcement may be needed too. Native validation helps with simple omissions but cannot replace the server's rules. A server round trip costs more than local feedback, yet it makes the authoritative decision visible and allows a useful response when script is unavailable. Retest the form with keyboard-only navigation, corrected values, and a successful submission.</p>"
            "<h3>Common Mistakes</h3><ul><li>Do not clear correct fields after one field fails.</li><li>Do not identify errors only by color or a generic message.</li><li>Do not trust the returned value without escaping it into the right HTML context.</li></ul>"
            "<h2>Connected lessons</h2><ul>" + linked(["html/aria-invalid-errors", "html/form-help-and-errors", "html/form-validation", "html/hidden-csrf-fields"]) + "</ul>"
        ),
        "related": ["html/aria-invalid-errors", "html/form-help-and-errors", "html/form-validation", "html/hidden-csrf-fields"],
    },
]

project_hub = by_path["html/html-tutorial/project"]
for index, item in enumerate(projects):
    assert item["path"] not in by_path
    row = copy.deepcopy(by_path["html/receipt-index-project"])
    row.update(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + item["path"])),
        path=item["path"], title=item["title"], summary=item["summary"], body=item["body"],
        subject=project_hub["subject"], tags=["html", "project"], sort_order=2500 + index,
        created_at=stamp, updated_at=stamp, published_at=stamp,
    )
    row["data"] = {"kind": "project", "reading_minutes": 9, "author_path": "authors/aitrove-editorial",
                   "subject_root": "html/html-tutorial", "section_path": "html/html-tutorial/project",
                   "content_format": "html", "seo_ready": True,
                   "related": [{"path": path, "title": by_path[path]["title"]} for path in item["related"]]}
    rows.append(row)
    by_path[row["path"]] = row
    for related_path in item["related"]:
        target = by_path[related_path]
        target["body"] += '<p><a href="/' + row["path"] + '">Apply this in ' + html.escape(row["title"]) + "</a>.</p>"
        target["data"].setdefault("related", []).append({"path": row["path"], "title": row["title"]})
        target["updated_at"] = stamp

catalog = by_path["html/web-development-projects"]
read_only = ["html/receipt-index-project", "html/receipt-dashboard-project", "html/multilingual-case-project", "html/incident-evidence-project"]
forms = ["html/receipt-review-form-project", "html/inspection-intake-project", "html/server-error-response-project"]
catalog["title"] = "HTML projects: build readable records and honest forms"
catalog["summary"] = "Seven applied HTML projects, from read-only evidence pages to server-rendered form errors."
catalog["body"] = (
    "<p>An HTML project should prove that its document, links, controls, and text alternatives make sense before visual polish or client-side enhancement. These seven projects separate read-only records from forms that need a real server.</p>"
    "<h2>Start with a readable record</h2><p>Build the receipt index first. Move to the dashboard when its source order and numbers remain intelligible without CSS. The multilingual case page adds a different text-direction problem. The incident evidence page adds a table, captions, and a descriptive transcript; it should still explain the case if media never loads.</p><ul>" + linked(read_only) + "</ul>"
    "<h2>Then handle a decision</h2><p>The receipt review form shows a bounded state-changing POST. The inspection intake form adds file and field constraints. The error response project asks what the server sends back when those constraints fail. Do not present any of these forms as a working service until the routes, persistence, permission checks, request protection, and tests exist.</p><ul>" + linked(forms) + "</ul>"
    '<pre><code class="language-html">' + html.escape('''<main>
  <h1>Inspection I-47 project checklist</h1>
  <ol>
    <li>Read the page with styles and scripts disabled.</li>
    <li>Follow every link and label by keyboard.</li>
    <li>Submit an empty form, then repair one field.</li>
    <li>Check media alternatives and narrow-screen order.</li>
  </ol>
</main>''', quote=False) + "</code></pre>"
    "<h2>Cost and verification</h2><p>Static markup is cheap. Asset delivery, content revisions, and server behavior are not. For each project, record which paths and files are illustrative, then replace them with working resources before public use. A passing HTML parser check cannot prove correct focus movement, spoken table associations, upload handling, or print layout. Use a real browser and assistive technology for those final checks. Keep the CSS and JavaScript layers separate so a structural mistake is not hidden by presentation.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not call a static form a completed transaction.</li><li>Do not use a diagram, clip, or color as the only evidence of a result.</li><li>Do not add a second page that repeats the same browser contract without a new testable decision.</li></ul>"
    "<h2>Connected lessons</h2><ul>" + linked(["html/landmarks", "html/table-caption-and-summary", "html/form-help-and-errors", "html/video-descriptive-transcript"]) + "</ul>"
)
catalog["data"]["related"] = [
    {"path": path, "title": by_path[path]["title"]} for path in read_only + forms
]
catalog["updated_at"] = stamp

project_hub["data"]["modules"] = [
    {"title": "Choose a project", "summary": "Select a distinct browser or application contract.", "lessons": [catalog["path"]]},
    {"title": "Read-only records", "summary": "Documents, tables, languages, and media alternatives.", "lessons": read_only},
    {"title": "Forms and responses", "summary": "Native controls and the server contract behind them.", "lessons": forms},
]
project_hub["body"] = (
    "<p>Build a document that remains readable before styling, then add a form only when its server contract is clear.</p>"
    "<h2>Choose a project</h2><ul>" + linked([catalog["path"]]) + "</ul>"
    "<h2>Read-only records</h2><ul>" + linked(read_only) + "</ul>"
    "<h2>Forms and responses</h2><ul>" + linked(forms) + "</ul>"
    '<p><a href="/html/html-tutorial">Return to the HTML tutorial</a>.</p>'
    "<h3>Common Mistakes</h3><p>Illustrative assets and endpoints are not a deployed case service. Check the behavior boundary in each project.</p>"
)
project_hub["updated_at"] = stamp

review_paths = [
    "html/button-type-default", "html/readonly-vs-disabled", "html/dialog-form-method",
    "html/draft-formnovalidate", "html/file-accept-hint", "html/telephone-input",
    "html/textarea-wrap-submission", "html/table-caption-and-summary",
    "html/video-descriptive-transcript", "html/aria-invalid-errors",
    "html/submitter-name-value", "html/image-submit-button",
]
questions = [
    ("A help button is placed inside an inspection form. Which type prevents an accidental POST?", ["reset", "button", "submit"], 1, "type=button gives the control no form-submission action."),
    ("Which value is normally omitted from submitted form data?", ["A readonly text field", "A named enabled textarea", "A disabled input"], 2, "Disabled controls are not successful form controls; readonly values can be submitted."),
    ("What does method=dialog do for a form inside a dialog?", ["Closes the dialog without a network submission", "Persists the decision", "Opens a new page"], 0, "The dialog method closes the panel; saving requires a separate application action."),
    ("A draft button has formnovalidate. Which check remains necessary?", ["No checks of any kind", "Server authorization and draft validation", "Only CSS validity styles"], 1, "Formnovalidate skips native browser constraint checks for that submission, not server rules."),
    ("What does accept on a file input establish?", ["A picker hint", "A server file-size limit", "Proof of the file's contents"], 0, "The server still needs to inspect size, type, content, and storage policy."),
    ("Why is type=number a poor choice for a telephone identifier?", ["It has no label support", "It blocks form submission", "It treats plus signs and leading zeroes as numeric formatting"], 2, "A telephone identifier is text, not a quantity."),
    ("When can a textarea add line breaks to the submitted value?", ["With wrap=soft", "With wrap=hard and cols", "Whenever CSS wraps the line"], 1, "Hard wrapping changes the submitted text according to its declared character width."),
    ("What is the caption's primary job in a data table?", ["Name the table", "Replace header cells", "Hide complex columns"], 0, "A caption identifies the table; headers still associate its cells."),
    ("What belongs in a descriptive video transcript beyond spoken words?", ["Only the file size", "Important visual action and meaningful sound", "Only a link to the clip"], 1, "A descriptive transcript records information needed to understand the media without playback."),
    ("A server rejects a case code. What should accompany aria-invalid=true?", ["A nearby linked repair instruction", "Only a red border", "An empty placeholder"], 0, "The state identifies a failure; text tells the user how to fix it."),
    ("Two named submit buttons share one form. Which value is normally submitted?", ["Both button values", "Neither value", "The activated submitter's value"], 2, "The submitter contributes its name and value; the backend still validates the choice."),
    ("What should alt text on an image submit button identify?", ["The image file extension", "The button action", "Only its pixel colors"], 1, "The alternative is the functional label when the image cannot be used."),
]
assert len(questions) == 12 and all(len(set(options)) == 3 for _, options, _, _ in questions)
quiz_path = "quizzes/html-production-review"
assert quiz_path not in by_path
quiz_hub = by_path["html/quizzes"]
quiz = copy.deepcopy(by_path["quizzes/html-document-structure"])
quiz.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + quiz_path)),
    path=quiz_path, title="HTML production decisions quiz",
    summary="Twelve explained checks on native browser behavior and server responsibilities.",
    body=("<p>Check the decision boundaries behind forms, tables, media, and input controls before using them in an application.</p>"
          "<h2>Review the lessons</h2><ul>" + linked(review_paths) + "</ul>"
          "<h3>Common Mistakes</h3><p>Passing a markup quiz does not prove that a route, asset, or authenticated server action exists.</p>"),
    sort_order=3005, created_at=stamp, updated_at=stamp, published_at=stamp,
)
quiz["data"] = {
    "subject_root": "html/html-tutorial", "section_path": "html/quizzes", "content_format": "html",
    "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
    "related": [{"path": path, "title": by_path[path]["title"]} for path in review_paths],
    "questions": [{"prompt": prompt, "options": options, "answer": answer, "explanation": explanation}
                  for prompt, options, answer, explanation in questions],
}
rows.append(quiz)
by_path[quiz_path] = quiz
quiz_hub["data"]["modules"].append({"title": quiz["title"], "summary": quiz["summary"], "lessons": [quiz_path]})
quiz_hub["body"] = quiz_hub["body"].replace(
    "<h3>Common Mistakes</h3>",
    '<h2>Applied review</h2><ul><li><a href="/' + quiz_path + '">' + quiz["title"] + "</a></li></ul><h3>Common Mistakes</h3>",
    1,
)
quiz_hub["updated_at"] = stamp

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(projects), "projects and one quiz")
