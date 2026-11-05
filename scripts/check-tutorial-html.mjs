import assert from "node:assert/strict";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { toJsxRuntime } from "hast-util-to-jsx-runtime";
import { Fragment, jsx, jsxs } from "react/jsx-runtime";
import { parseTutorialHtml } from "../src/lib/tutorial-html.ts";

const render = (source) =>
  renderToStaticMarkup(toJsxRuntime(parseTutorialHtml(source), { Fragment, jsx, jsxs }));
const program =
  "import java.util.LinkedList;\n\npublic class TaskQueueDemo {\n    public static void main(String[] args) {\n        LinkedList<String> tasks = new LinkedList<>();\n    }\n}";
const codeHtml = program.replaceAll("<", "&lt;").replaceAll(">", "&gt;");
const codeTree = parseTutorialHtml(`<pre><code class="language-java">${codeHtml}</code></pre>`);
assert.equal(codeTree.children.length, 1);
const pre = codeTree.children[0];
assert.equal(pre.tagName, "pre");
assert.equal(pre.children.length, 1);
assert.equal(pre.children[0].tagName, "code");
assert.equal(pre.children[0].children[0].value, program);
assert.equal(
  render(`<pre><code class="language-java">${codeHtml}</code></pre>`),
  `<pre><code class="language-java">${codeHtml}</code></pre>`,
);
const dangerous = render(
  '<p onclick="alert(1)">Lesson</p><script>alert(2)</script><iframe src="https://invalid.test"></iframe><img src=x onerror="alert(3)"><a href="javascript:alert(4)">link</a><style>body{display:none}</style><pre><code class="language-java evil" style="color:red">List&lt;String&gt; jobs;</code></pre>',
);
assert.ok(
  !/onclick|onerror|javascript:|<script|<iframe|<img|<style|style=|evil/.test(dangerous),
  dangerous,
);
assert.ok(dangerous.includes('class="language-java"'));
assert.ok(dangerous.includes("List&lt;String&gt; jobs;"));
const lesson = render(
  "<p>LinkedList stores linked nodes.</p><h2>Operations</h2><h3>Common Mistakes</h3><ul><li><strong>Indexing:</strong> requires traversal.</li></ul>",
);
assert.ok(lesson.includes("<h3>Common Mistakes</h3>"));
const links = render(
  '<p><a href="/java/hashmap">Map</a><a href="//external.test">External</a><a href="/courses/archive">Course</a><a href="https://external.test">Outside</a><a href="/java/hashmap%5c">Encoded</a></p>',
);
assert.ok(links.includes('href="/java/hashmap"'));
assert.equal((links.match(/href=/g) ?? []).length, 1);
console.log(
  JSON.stringify({ safeHtml: true, codePreserved: true, unsafeTagsAndAttributesRemoved: true }),
);
