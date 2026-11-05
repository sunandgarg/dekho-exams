"""Check the HTML curriculum's structure, routes, and example associations."""

import html
import base64
import hashlib
import json
import pathlib
import re
from html.parser import HTMLParser


root = pathlib.Path(__file__).resolve().parents[1]
entries = json.loads((root / "src/data/fixtures.json").read_text())
lookup = {entry["path"]: entry for entry in entries}
assert len(lookup) == len(entries), "duplicate canonical route"
selected = [entry for entry in entries if entry["path"].startswith(("html/", "quizzes/html-")) or entry["path"] == "quizzes/web-foundations"]
allowed = {"p", "h2", "h3", "ul", "li", "strong", "pre", "code", "a"}
banned = re.compile(
    r"\b(delve|leverage|harness|foster|streamline|showcase|navigate|demystify|"
    r"furthermore|moreover|additionally|robust|crucial|pivotal|multifaceted|"
    r"bespoke|seamless|dynamic|quintessential|nuanced|powerful|versatile)\b", re.I
)


class BodyParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        assert tag in allowed, tag
        if tag == "a":
            assert not any(parent in ("pre", "code") for parent in self.stack)
            assert len(attrs) == 1 and attrs[0][0] == "href"
            target = attrs[0][1]
            assert target.startswith("/"), target
            assert target[1:].split("#")[0] in lookup, target
            self.links.append(target)
        elif tag == "code":
            assert len(attrs) == 1 and attrs[0][0] == "class"
            assert attrs[0][1].startswith("language-")
        else:
            assert not attrs, (tag, attrs)
        self.stack.append(tag)

    def handle_endtag(self, tag):
        assert self.stack.pop() == tag, tag


class ExampleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.labels = []
        self.references = []
        self.header_ids = []
        self.header_references = []
        self.form_ids = []
        self.form_references = []
        self.datalist_ids = []
        self.datalist_references = []
        self.popover_ids = []
        self.popover_references = []
        self.fragment_references = []
        self.map_names = []
        self.map_references = []
        self.output_references = []
        self.command_references = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "label" and "for" in attrs:
            self.labels.append(attrs["for"])
        if tag == "th" and "id" in attrs:
            self.header_ids.append(attrs["id"])
        if tag == "form" and "id" in attrs:
            self.form_ids.append(attrs["id"])
        if tag == "datalist" and "id" in attrs:
            self.datalist_ids.append(attrs["id"])
        if "popover" in attrs and "id" in attrs:
            self.popover_ids.append(attrs["id"])
        for key in ("aria-labelledby", "aria-describedby"):
            if key in attrs:
                self.references.extend(attrs[key].split())
        if "headers" in attrs:
            self.header_references.extend(attrs["headers"].split())
        if "form" in attrs:
            self.form_references.append(attrs["form"])
        if "list" in attrs:
            self.datalist_references.append(attrs["list"])
        if "popovertarget" in attrs:
            self.popover_references.append(attrs["popovertarget"])
        if "commandfor" in attrs:
            self.command_references.append(attrs["commandfor"])
        if tag == "map" and "name" in attrs:
            self.map_names.append(attrs["name"])
        if "usemap" in attrs:
            assert attrs["usemap"].startswith("#"), attrs["usemap"]
            self.map_references.append(attrs["usemap"][1:])
        if tag == "output" and "for" in attrs:
            self.output_references.extend(attrs["for"].split())
        if "href" in attrs and attrs["href"].startswith("#"):
            self.fragment_references.append(attrs["href"][1:])
        for key in ("href", "src", "action"):
            if key in attrs:
                assert not attrs[key].lower().startswith(("javascript:", "http:", "https:"))


links = []
module_paths = set()
articles = []
questions = 0
for entry in selected:
    path = entry["path"]
    assert entry["status"] == "published", path
    assert entry["data"]["subject_root"] == "html/html-tutorial", path
    assert entry["data"]["section_path"] in lookup, path
    assert entry["data"]["content_format"] == "html", path
    assert entry["data"]["seo_ready"] is True, path
    assert "http://" not in entry["body"] and "https://" not in entry["body"], path
    assert not banned.search(re.sub(r"<[^>]*>", " ", entry["body"])), path
    parser = BodyParser()
    parser.feed(entry["body"])
    assert not parser.stack, path
    links.extend(parser.links)
    for related in entry["data"].get("related", []):
        assert related["path"] in lookup, (path, related)
    if entry["type"] == "subject":
        hub_lessons = [target for module in entry["data"]["modules"] for target in module["lessons"]]
        assert len(hub_lessons) == len(set(hub_lessons)), (path, "duplicate hub lesson")
        for module in entry["data"]["modules"]:
            assert module["lessons"], path
            for target in module["lessons"]:
                assert lookup[target]["subject"] == entry["subject"], (path, target)
                module_paths.add(target)
    elif entry["type"] == "quiz":
        assert len(entry["data"]["questions"]) == 12, path
        for question in entry["data"]["questions"]:
            assert len(question["options"]) == len(set(question["options"])) == 3
            assert question["answer"] in range(3) and question["explanation"]
            assert not banned.search(question["prompt"] + " " + question["explanation"])
        questions += 12
    else:
        articles.append(entry)
        assert entry["body"].startswith("<p>"), path
        assert "<h3>Common Mistakes</h3>" in entry["body"], path
        samples = re.findall(r'<pre><code class="language-html">([\s\S]*?)</code></pre>', entry["body"])
        assert len(samples) == 1, path
        sample = html.unescape(samples[0])
        assert "<" in sample and ">" in sample, path
        example = ExampleParser()
        example.feed(sample)
        assert len(example.ids) == len(set(example.ids)), (path, "duplicate sample id")
        assert set(example.labels + example.references) <= set(example.ids), (path, example.labels, example.references, example.ids)
        for references, targets, label in (
            (example.header_references, example.header_ids, "table headers"),
            (example.form_references, example.form_ids, "form owner"),
            (example.datalist_references, example.datalist_ids, "datalist"),
            (example.popover_references, example.popover_ids, "popover"),
            (example.fragment_references, example.ids, "fragment"),
            (example.map_references, example.map_names, "image map"),
            (example.output_references, example.ids, "output source"),
            (example.command_references, example.ids, "command target"),
        ):
            assert set(references) <= set(targets), (path, label, references, targets)
        prose = re.sub(r"<pre>[\s\S]*?</pre>", "", entry["body"])
        prose = re.sub(r"<[^>]*>", " ", prose)
        assert len(prose.split()) >= 105, (path, len(prose.split()))
        if path == "html/subresource-integrity":
            expected = base64.b64encode(hashlib.sha384((root / "public/fonts/fonts.css").read_bytes()).digest()).decode()
            assert 'href="/fonts/fonts.css"' in sample, path
            assert 'integrity="sha384-' + expected + '"' in sample, (path, "stale integrity digest")

assert module_paths == {entry["path"] for entry in selected if entry["type"] != "subject"}, "unlinked curriculum page"
root_hub = lookup["html/html-tutorial"]
tabs = root_hub["data"]["resource_tabs"]
assert {tab["path"] for tab in tabs} == {entry["path"] for entry in selected if entry["type"] == "subject"}
assert len(tabs) == len({tab["path"] for tab in tabs})
assert len({entry["title"] for entry in selected}) == len(selected)
report = {"passed": True, "articles": len(articles),
          "hubs": sum(entry["type"] == "subject" for entry in selected),
          "quizBanks": sum(entry["type"] == "quiz" for entry in selected),
          "questions": questions, "bodyLinks": len(links),
          "curriculumOrphans": 0, "htmlSamplesChecked": len(articles)}
(root / "work/html-content-validation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report))
