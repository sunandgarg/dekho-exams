"""Check the CSS curriculum's public structure, links, and quiz coverage."""

import html
import json
import pathlib
import re
from html.parser import HTMLParser


root = pathlib.Path(__file__).resolve().parents[1]
entries = json.loads((root / "src/data/fixtures.json").read_text())
lookup = {entry["path"]: entry for entry in entries}
assert len(lookup) == len(entries), "duplicate route"
selected = [entry for entry in entries if entry["path"].startswith(("css/", "quizzes/css-"))]
allowed = {"p", "h2", "h3", "ul", "li", "strong", "pre", "code", "a"}
banned = re.compile(
    r"\b(delve|leverage|harness|foster|streamline|showcase|navigate|demystify|"
    r"robust|crucial|pivotal|multifaceted|bespoke|seamless|dynamic|"
    r"quintessential|nuanced)\b", re.I
)


class BodyParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        assert tag in allowed, tag
        if tag == "a":
            assert len(attrs) == 1 and attrs[0][0] == "href", attrs
            target = attrs[0][1]
            assert target.startswith("/") and target[1:].split("#")[0] in lookup, target
            self.links.append(target)
        elif tag == "code":
            assert len(attrs) == 1 and attrs[0][0] == "class", attrs
            assert attrs[0][1] in {"language-css", "language-html"}, attrs
        else:
            assert not attrs, attrs
        self.stack.append(tag)

    def handle_endtag(self, tag):
        assert self.stack.pop() == tag, tag


module_paths = set()
links = []
samples = []
articles = []
questions = 0
for entry in selected:
    path = entry["path"]
    assert entry["status"] == "published", path
    assert entry["data"]["subject_root"] == "css/css-tutorial", path
    assert entry["data"]["section_path"] in lookup, path
    assert entry["data"]["content_format"] == "html", path
    assert entry["data"]["seo_ready"] is True, path
    body = entry["body"]
    assert "http://" not in body and "https://" not in body, path
    prose = re.sub(r"<pre>[\s\S]*?</pre>", "", body)
    prose = html.unescape(re.sub(r"<[^>]*>", " ", prose))
    assert not banned.search(prose), path
    parser = BodyParser()
    parser.feed(body)
    assert not parser.stack, path
    links.extend(parser.links)
    for related in entry["data"].get("related", []):
        assert related["path"] in lookup and related["title"] == lookup[related["path"]]["title"], (path, related)

    if entry["type"] == "subject":
        lessons = [target for module in entry["data"]["modules"] for target in module["lessons"]]
        assert len(lessons) == len(set(lessons)), path
        for module in entry["data"]["modules"]:
            assert module["lessons"], path
            for target in module["lessons"]:
                assert lookup[target]["subject"] == entry["subject"], (path, target)
                assert target not in module_paths, (path, target)
                module_paths.add(target)
    elif entry["type"] == "quiz":
        assert len(entry["data"]["questions"]) == 12, path
        for question in entry["data"]["questions"]:
            assert len(question["options"]) == len(set(question["options"])) == 3, path
            assert question["answer"] in range(3) and question["explanation"], path
            assert not banned.search(question["prompt"] + " " + question["explanation"]), path
        questions += 12
    else:
        articles.append(entry)
        assert body.startswith("<p>") and body.count("<h3>Common Mistakes</h3>") == 1, path
        code_blocks = re.findall(r'<pre><code class="(language-(?:css|html))">([\s\S]*?)</code></pre>', body)
        assert len(code_blocks) == 1, path
        language, escaped_sample = code_blocks[0]
        assert language == ("language-html" if path == "css/authoring-and-loading" else "language-css"), path
        samples.append({"path": path, "language": language[9:], "sample": html.unescape(escaped_sample)})
        assert len(prose.split()) >= 140, (path, len(prose.split()))

assert module_paths == {entry["path"] for entry in selected if entry["type"] != "subject"}, "unlinked CSS page"
tabs = lookup["css/css-tutorial"]["data"]["resource_tabs"]
assert {tab["path"] for tab in tabs} == {entry["path"] for entry in selected if entry["type"] == "subject"}
assert len(tabs) == len({tab["path"] for tab in tabs})
assert len({entry["title"] for entry in selected}) == len(selected)
report = {"passed": True, "articles": len(articles),
          "hubs": sum(entry["type"] == "subject" for entry in selected),
          "quizBanks": sum(entry["type"] == "quiz" for entry in selected),
          "questions": questions, "bodyLinks": len(links),
          "curriculumOrphans": 0, "cssSamples": sum(item["language"] == "css" for item in samples)}
(root / "work/css-content-validation.json").write_text(json.dumps(report, indent=2) + "\n")
(root / "work/css-samples-for-validation.json").write_text(json.dumps(samples, indent=2) + "\n")
print(json.dumps(report))
