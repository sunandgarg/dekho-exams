"""Extend the Spring web/security quiz with checked upload and probe cases."""
from __future__ import annotations

import datetime
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILE = ROOT / "src/data/fixtures.json"
rows = json.loads(FILE.read_text())
quiz = next(row for row in rows if row["path"] == "quizzes/spring-web-security")
by_path = {row["path"]: row for row in rows}
questions = [
    ("A multipart part says its original filename is ../../outside.csv. Which path does the checked controller write?",
     ["A generated file inside the temporary storage root", "The parent directory named by the client", "No file because every slash is rejected"], 0,
     "The accepted request ignores the supplied filename for storage and verifies the generated path."),
    ("A part claims text/csv but contains HTML. What does the local upload fixture return?",
     ["200 because MIME text is trusted", "422 with no staged file", "503 because readiness failed"], 1,
     "The checked header gate rejects the bytes before creating a file; the MIME declaration is caller controlled."),
    ("What does standalone MockMvc fail to prove for an oversized multipart request?",
     ["The controller's own 413 decision", "Servlet and reverse-proxy request-size enforcement", "That rejected requests leave the JUnit directory empty"], 1,
     "MockMultipartFile already holds the bytes and does not run the deployed parser or proxy."),
    ("The test-only importStore indicator changes from UP to DOWN. Which response pair is checked?",
     ["Readiness 503, liveness 200", "Readiness 200, liveness 503", "Both routes become 401"], 0,
     "Only the readiness group includes the indicator; the process liveness signal stays healthy."),
    ("Nested health paths are public in the source kit. What happens to anonymous GET /api/receipts?",
     ["It also becomes public", "It remains 401", "It becomes 503"], 1,
     "The filter matcher permits only the health path and nested health groups before requiring authentication elsewhere."),
    ("What remains outside the checked multipart fixture?",
     ["Its generated filename assertion", "A deployed servlet parser, durable storage and full CSV row validation", "Its local UTF-8 rejection"], 1,
     "The controller is standalone; no production upload route or parser pipeline has been deployed."),
]
assert len(quiz["data"]["questions"]) == 18
quiz["data"]["questions"].extend(dict(prompt=prompt, options=options, answer=answer, explanation=explanation)
    for prompt, options, answer, explanation in questions)
quiz["summary"] = "Twenty-four explained questions on Spring MVC, JWT, uploads and probe boundaries."
related = ["spring/multipart-receipt-import", "spring/upload-byte-budget",
    "spring/upload-generated-filename", "spring/upload-mockmvc-boundary",
    "spring/readiness-health-group", "spring/health-probe-security"]
links = "".join('<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>"
    for path in related)
quiz["body"] = quiz["body"].replace("</ul><h2>Check your reasoning</h2>",
    links + "</ul><h2>Check your reasoning</h2>")
quiz["updated_at"] = datetime.datetime.now(datetime.UTC).isoformat()
FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"quiz": quiz["path"], "questions": len(quiz["data"]["questions"])}))
