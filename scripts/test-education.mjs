import assert from "node:assert/strict";
import { registerHooks } from "node:module";
import { test } from "node:test";
import { readFileSync } from "node:fs";

// Node's type stripping keeps these checks on the real source, without a test framework.
registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier.startsWith("@/") && specifier.endsWith(".json"))
      return nextResolve(new URL(`../src/${specifier.slice(2)}`, import.meta.url).href, context);
    if (
      specifier.startsWith("./") &&
      !/\.[a-z]+$/.test(specifier) &&
      context.parentURL?.includes("/src/lib/")
    )
      return nextResolve(`${specifier}.ts`, context);
    return nextResolve(specifier, context);
  },
  // App code imports JSON through Vite without an import attribute; Node needs one.
  load(url, context, nextLoad) {
    if (url.endsWith(".json") && context.importAttributes?.type !== "json")
      return {
        format: "module",
        source: `export default ${readFileSync(new URL(url), "utf8")};`,
        shortCircuit: true,
      };
    return nextLoad(url, context);
  },
});
const catalog = await import("../src/lib/education-catalog.ts");
const { SUBJECT_DIRECTORY, HOME_SHORTCUTS, directoryItem } =
  await import("../src/lib/subject-directory.ts");
const { default: directoryReference } = await import("../src/data/khan-course-reference.json", {
  with: { type: "json" },
});
const { parseProgress } = await import("../src/lib/learning-progress.ts");
const { EXAM_GUIDES } = await import("../src/lib/exam-update-guides.ts");
const { default: languageArt } = await import("../src/data/language-art.json", {
  with: { type: "json" },
});
test("all class and language discovery artwork exists at stable image dimensions", () => {
  assert.deepEqual(Object.keys(languageArt).sort(), catalog.LANGUAGES.map(([slug]) => slug).sort());
  const names = [
    ...Array.from({ length: 12 }, (_, index) => `class-${index + 1}`),
    ...Object.keys(languageArt).map((slug) => `language-${slug}`),
  ];
  for (const name of names) {
    const image = readFileSync(new URL(`../public/images/discovery/${name}.png`, import.meta.url));
    assert.equal(image.subarray(1, 4).toString(), "PNG", name);
    assert.equal(image.readUInt32BE(16), 192, name);
    assert.equal(image.readUInt32BE(20), 192, name);
    assert.ok(image.length < 25000, `${name}: artwork should stay lightweight`);
  }
});
const {
  EDUCATION_PAGES: pages,
  RESOURCES: resources,
  educationPage,
  resourceById,
  EDUCATION_ALIASES: aliases,
} = catalog;

test("canonical route ownership, parents, links and IDs are unique and resolvable", () => {
  assert.equal(new Set(pages.map((p) => p.path)).size, pages.length);
  assert.equal(new Set(resources.map((r) => r.id)).size, resources.length);
  for (const page of pages) {
    assert.match(page.path, /^\/[a-z0-9-]+(?:\/[a-z0-9-]+)*$/);
    assert.ok(page.parent === "/" || educationPage(page.parent), page.path);
    for (const path of page.children) assert.ok(educationPage(path), `${page.path} -> ${path}`);
    for (const section of page.sections ?? [])
      for (const path of section.paths) assert.ok(educationPage(path), `${page.path} -> ${path}`);
    for (const id of page.resourceIds) assert.ok(resourceById(id), `${page.path} -> ${id}`);
    const visited = new Set();
    for (let p = page; p; p = educationPage(p.parent)) {
      assert.ok(!visited.has(p.path), "breadcrumb cycle");
      visited.add(p.path);
    }
  }
  for (const r of resources) {
    assert.match(r.id, /^pp-\d{4}$/);
    assert.equal(educationPage(r.canonicalPath)?.resourceId, r.id);
    assert.ok(
      r.lesson.questions.every(
        (q) => q.answer >= 0 && q.answer < q.choices.length && q.explanation,
      ),
    );
  }
});
test("contextual study links are relevant, unique and canonical", () => {
  for (const page of pages) {
    const links = catalog.relatedEducationPages(page);
    assert.ok(links.length <= 7, page.path);
    assert.equal(new Set(links.map((link) => link.path)).size, links.length, page.path);
    for (const link of links) {
      assert.notEqual(link.path, page.path);
      assert.equal(educationPage(link.path), link);
    }
  }
  const classLinks = catalog.relatedEducationPages(
    educationPage("/class-10/maths/quadratic-equations"),
  );
  assert.ok(classLinks.some((link) => link.path === "/ncert/class-10/maths"));
  assert.ok(classLinks.some((link) => link.path === "/cbse/class-10"));
  const updateLinks = catalog.relatedEducationPages(educationPage("/exam-updates/results"));
  assert.ok(updateLinks.some((link) => link.path === "/exam-updates/date-sheets"));
});
test("lesson drafts include distinct teaching guidance", () => {
  for (const field of ["whyItWorks", "commonMistake"]) {
    const entries = resources.map((resource) => resource.lesson[field]?.trim());
    assert.ok(
      entries.every((entry) => entry && entry.length > 50),
      field,
    );
    assert.equal(new Set(entries).size, resources.length, field);
  }
});
test("all requested collections, grades and languages have destinations", () => {
  for (let grade = 1; grade <= 12; grade++)
    assert.ok(educationPage(`/class-${grade}`)?.resourceIds.length);
  for (const [path] of catalog.HOME_CATEGORIES) assert.ok(educationPage(path));
  for (const [slug] of catalog.LANGUAGES) assert.ok(educationPage(`/ncert/${slug}`));
  assert.equal(catalog.HOME_CATEGORIES.filter(([p]) => p === "/gate").length, 1);
  for (const group of catalog.EDUCATION_NAV)
    for (const section of group.sections)
      for (const [, path] of section.links) assert.ok(educationPage(`/${path}`));
});
test("exam update guides link only to official publishers and stay in preview", () => {
  assert.deepEqual(
    educationPage("/exam-updates")?.children,
    EXAM_GUIDES.map((guide) => guide.path),
  );
  for (const guide of EXAM_GUIDES) {
    const page = educationPage(guide.path);
    assert.ok(page, guide.path);
    assert.equal(page.reviewed, false);
    assert.ok(guide.sections.length);
    for (const section of guide.sections)
      for (const link of section.links) {
        assert.match(
          new URL(link.path).hostname,
          /^(?:www\.)?(?:cbse\.gov\.in|cbseacademic\.nic\.in|cbseresults\.nic\.in|nta\.ac\.in|jeemain\.nta\.nic\.in|neet\.nta\.nic\.in)$/,
        );
        assert.ok(page.sources.some((source) => source.path === link.path));
      }
  }
  assert.ok(
    educationPage("/ncert")?.sources.some(
      (source) => source.path === "https://ncert.nic.in/syllabus.php",
    ),
  );
});
test("class-first NCERT, language and board directories keep chapters before papers", () => {
  assert.deepEqual(
    educationPage("/ncert")?.sections?.[0].paths,
    catalog.GRADES_FOR_FILTER.map((grade) => `/ncert/class-${grade}`),
  );
  for (const grade of catalog.GRADES_FOR_FILTER) {
    const ncert = educationPage(`/ncert/class-${grade}`);
    assert.ok(ncert);
    assert.equal(ncert.parent, "/ncert");
    assert.equal(ncert.sections[0].title, "Subjects");
    assert.equal(ncert.sections.at(-1).title, "Papers and practice");
    for (const [kind] of catalog.RESOURCE_TYPES.filter(([slug]) => slug.startsWith("ncert"))) {
      const canonical = `/ncert/class-${grade}/${kind.slice(6)}`;
      assert.equal(educationPage(canonical)?.parent, `/ncert/class-${grade}`);
      assert.equal(aliases[`/${kind}/class-${grade}`], canonical);
    }
    for (const [language] of catalog.LANGUAGES) {
      const page = educationPage(`/ncert/${language}/class-${grade}`);
      assert.equal(page?.parent, `/ncert/${language}`);
      assert.equal(page.sections[0].title, "Chapters");
      assert.equal(page.sections.at(-1).title, "Papers and practice");
    }
    for (const [state] of catalog.STATES) {
      const page = educationPage(`/state-boards/${state}/class-${grade}`);
      assert.equal(page?.parent, `/state-boards/${state}`);
      assert.equal(page.sections[0].title, "Subjects");
      assert.equal(page.sections.at(-1).title, "Papers and practice");
    }
  }
});
test("class, board, subject and chapter navigation stays connected", () => {
  for (const grade of catalog.GRADES_FOR_FILTER) {
    const classPage = educationPage(`/class-${grade}`);
    assert.equal(classPage.sections[0].title, "Boards & books");
    assert.equal(classPage.sections[1].title, "Subjects");
    for (const boardPath of classPage.sections[0].paths) {
      const board = educationPage(boardPath);
      assert.ok(board, boardPath);
      assert.equal(board.sections[0].title, "Subjects");
      for (const subjectPath of board.sections[0].paths) {
        const subject = educationPage(subjectPath);
        assert.equal(subject?.parent, boardPath);
        assert.equal(subject.sections[0].title, "Chapters");
        for (const chapterPath of subject.sections[0].paths)
          assert.ok(educationPage(chapterPath)?.resourceId, chapterPath);
      }
    }
    for (const subjectPath of classPage.sections[1].paths)
      assert.equal(educationPage(subjectPath)?.parent, classPage.path);
  }
  assert.ok(educationPage("/class-1/english"));
  assert.ok(educationPage("/ncert/class-1/english"));
  assert.ok(educationPage("/cbse/class-1/english"));
  assert.ok(educationPage("/cisce/class-1/english"));
});
test("NCERT syllabus pages point to the official source without presenting draft lessons as syllabus", () => {
  for (const grade of catalog.GRADES_FOR_FILTER) {
    const syllabus = educationPage(`/ncert/class-${grade}/syllabus`);
    assert.ok(syllabus);
    assert.equal(syllabus.parent, `/ncert/class-${grade}`);
    assert.deepEqual(syllabus.resourceIds, []);
    assert.ok(
      syllabus.sources.some((source) => source.path === catalog.NCERT_SYLLABUS_SOURCE.path),
    );
  }
  for (const language of ["english", "hindi"]) {
    const classPage = educationPage(`/ncert/${language}/class-10`);
    assert.ok(classPage);
    assert.equal(classPage.parent, `/ncert/${language}`);
    const syllabus = educationPage(`/ncert/${language}/class-10/syllabus`);
    assert.equal(syllabus?.parent, classPage.path);
    assert.deepEqual(syllabus.resourceIds, []);
    assert.ok(
      syllabus.sources.some((source) => source.path === catalog.NCERT_SYLLABUS_SOURCE.path),
    );
  }
});
test("legacy aliases lead directly to a canonical page, never another alias", () => {
  for (const [from, to] of Object.entries(aliases)) {
    assert.ok(educationPage(to), from);
    assert.ok(!aliases[to]);
    assert.ok(!educationPage(from));
  }
  assert.equal(
    aliases["/study/class-10/quadratic-equations"],
    "/class-10/maths/quadratic-equations",
  );
  assert.ok(catalog.ownsEducationPath("/class-13"));
  assert.ok(catalog.ownsEducationPath("/ncert-solutions/nonexistent"));
  assert.equal(educationPage("/ncert-solutions/nonexistent"), undefined);
  assert.equal(catalog.ownsEducationPath("/java/java"), false);
});
test("publication gate prevents placeholder, unreviewed and private pages entering search", () => {
  assert.ok(pages.every((p) => !catalog.educationIndexable(p)));
  const approved = {
    ...resources[0],
    status: "published",
    author: "Test author",
    reviewer: "Test reviewer",
    reviewedAt: "2026-10-01",
  };
  assert.equal(catalog.resourceReady(approved), true);
  for (const change of [
    { reviewer: null },
    { reviewedAt: "invalid" },
    { rights: "pending" },
    { status: "preview" },
    { author: " " },
  ])
    assert.equal(catalog.resourceReady({ ...approved, ...change }), false);
});
test("browser progress rejects malformed, unknown and outdated data", () => {
  assert.deepEqual(parseProgress("invalid").saved, []);
  assert.deepEqual(parseProgress('{"version":2,"saved":["pp-0001"]}').saved, []);
  const p = parseProgress(
    JSON.stringify({
      version: 1,
      saved: ["missing", "pp-0001", "pp-0001"],
      recent: {},
      answers: { "pp-0001@1": { 0: 1, 1: 42, 99: 0 }, "pp-0001@0": { 0: 1 } },
    }),
  );
  assert.deepEqual(p.saved, ["pp-0001"]);
  assert.deepEqual(p.answers["pp-0001@1"], { 0: 1 });
  assert.equal(p.answers["pp-0001@0"], undefined);
});

test("all 18 reference dropdowns retain every option and valid local destinations", () => {
  assert.equal(SUBJECT_DIRECTORY.length, 18);
  assert.equal(
    SUBJECT_DIRECTORY.reduce((n, g) => n + g.items.length, 0),
    302,
  );
  assert.equal(HOME_SHORTCUTS.length, 6);
  for (const shortcut of HOME_SHORTCUTS) assert.ok(educationPage(shortcut.path));
  SUBJECT_DIRECTORY.forEach((group, index) => {
    assert.deepEqual(
      group.items.map((item) => item.referenceUrl),
      directoryReference.groups[index].items.map((item) => item.url),
    );
    assert.ok(educationPage(group.path), group.path);
    for (const item of group.items) {
      const href = new URL(item.href, "https://pencil2pen.com");
      assert.equal(href.pathname, group.path);
      assert.ok(directoryItem(href.pathname, href.searchParams.get("topic")));
      assert.equal(new URL(item.referenceUrl).origin, "https://www.khanacademy.org");
      assert.ok(item.id.length <= 80);
    }
  });
});

if (process.env.PENPENCIL_TEST_URL) {
  const base = new URL(process.env.PENPENCIL_TEST_URL);
  assert.ok(["localhost", "127.0.0.1"].includes(base.hostname), "HTTP smoke tests are local-only");
  test("every catalog route SSRs unique canonical metadata and a visible heading", async () => {
    for (const page of pages) {
      const response = await fetch(new URL(page.path, base));
      assert.equal(response.status, 200, page.path);
      const html = await response.text();
      assert.match(html, /<h1[^>]*>/, page.path);
      assert.ok(html.includes(`href="https://pencil2pen.com${page.path}"`), page.path);
      assert.equal((html.match(/rel="canonical"/g) ?? []).length, 1, page.path);
      assert.match(html, /name="robots" content="noindex,follow"/, page.path);
    }
  });
  test("HTTP redirects, preview sitemaps and genuine 404s", async () => {
    for (const [from, to] of Object.entries(aliases)) {
      const response = await fetch(new URL(`${from}?q=maths`, base), { redirect: "manual" });
      assert.equal(response.status, 301, from);
      assert.equal(new URL(response.headers.get("location"), base).pathname, to);
      assert.equal(new URL(response.headers.get("location"), base).search, "?q=maths");
    }
    for (const path of ["/class-13", "/class-10/maths/missing", "/ncert-solutions/missing"])
      assert.equal((await fetch(new URL(path, base))).status, 404, path);
    for (const path of ["/sitemap.xml", "/sitemap-education.xml"]) {
      const response = await fetch(new URL(path, base));
      assert.equal(response.status, 200);
      assert.ok(!(await response.text()).includes("<loc>"));
    }
    assert.equal(
      await (await fetch(new URL("/robots.txt", base))).text(),
      "User-agent: *\nDisallow: /\n",
    );
  });
  test("search retains numeric classes and does not mix subject results", async () => {
    const html = async (path) => await (await fetch(new URL(path, base))).text();
    assert.match(await html("/search?q=quadratic&grade=6"), /No matches/);
    assert.ok(!(await html("/search?q=quadratic&grade=10")).includes("No matches"));
    assert.ok((await html("/search?q=10")).includes("Quadratic equations by factorisation"));
    const maths = await html("/search?q=maths&grade=6");
    assert.ok(!maths.includes('href="/class-6/science/food-and-nutrients"'));
    assert.ok((await html("/search?q=kannada")).includes('href="/ncert/kannada"'));
  });
  test("homepage omits the two withdrawn subject groups", async () => {
    const html = await (await fetch(new URL("/", base))).text();
    assert.match(html, /id="trigger-ncert-maths"/);
    assert.match(html, /id="trigger-boards"/);
    assert.doesNotMatch(html, /id="trigger-explore-more"/);
    assert.doesNotMatch(html, /id="trigger-teachers"/);
    assert.equal(
      (
        html.match(
          /id="trigger-(?:ncert|state-boards|english|computer-science|economics|boards)[^"]*"/g,
        ) ?? []
      ).length,
      16,
    );
  });
  test("syllabus and study strategy appear at the top of education pages", async () => {
    for (const path of ["/ncert/class-12", "/ncert/english/class-10", "/ncert/hindi/class-10"]) {
      const html = await (await fetch(new URL(path, base))).text();
      assert.ok(html.includes('id="syllabus-spotlight"'), path);
      assert.ok(html.includes('id="study-strategy"'), path);
      assert.ok(html.includes(`href="${path}/syllabus"`), path);
      assert.ok(html.includes(catalog.NCERT_SYLLABUS_SOURCE.path), path);
      assert.ok(
        html.indexOf('id="syllabus-spotlight"') < html.indexOf('id="collection-section-0"'),
        path,
      );
    }
    for (const path of ["/class-10/maths/quadratic-equations", "/my-study"]) {
      const html = await (await fetch(new URL(path, base))).text();
      assert.ok(html.includes('id="study-strategy"'), path);
    }
  });
  test("internal pages lead with useful choices and honest study notes", async () => {
    const html = async (path) => await (await fetch(new URL(path, base))).text();
    const classes = await html("/classes");
    assert.ok(
      classes.indexOf("Choose your class. You can pick a board") <
        classes.indexOf('id="study-strategy"'),
    );
    assert.match(classes, /study-class-list/);
    assert.doesNotMatch(classes, /class="study-page-curriculum"/);
    assert.match(classes, /images\/discovery\/class-1\.png/);
    assert.ok(classes.indexOf('id="explore-collection"') < classes.indexOf('id="study-strategy"'));
    assert.doesNotMatch(classes, /1 lesson to explore/);
    assert.doesNotMatch(classes, /1 original lessons/);
    const classPage = await html("/class-1");
    assert.match(classPage, /class="study-state-boards"/);
    assert.ok(
      classPage.indexOf('id="collection-section-0"') < classPage.indexOf('id="study-strategy"'),
    );
    const emptySubject = await html("/class-1/english");
    assert.ok(
      emptySubject.indexOf('id="available-lessons"') < emptySubject.indexOf('id="study-strategy"'),
    );
    assert.match(emptySubject, /Use the contents page in your school book for now/);
    assert.match(emptySubject, /Read one paragraph aloud/);
    assert.match(emptySubject, /Easy slip: reading the same line again/);
    assert.match(await html("/class-1/maths"), /Easy slip: rushing to a formula/);
    const lesson = await html("/class-1/maths/counting-to-20");
    assert.match(lesson, /We have not checked which book edition it matches yet/);
    assert.match(lesson, /Easy slip: checking the answer too soon/);
  });
  test("directory selections stay noindex and expose an honest external reference", async () => {
    for (const group of SUBJECT_DIRECTORY) {
      for (const item of group.items) {
        const response = await fetch(new URL(item.href, base));
        assert.equal(response.status, 200, item.href);
        const html = await response.text();
        assert.ok(
          html.includes("Dekhoexams lessons for this specific course are not published yet."),
          item.href,
        );
        assert.ok(html.includes(`href="${item.referenceUrl}"`), item.href);
        assert.ok(html.includes(`href="https://pencil2pen.com${group.path}"`), item.href);
        assert.match(html, /name="robots" content="noindex,follow"/);
      }
    }
  });
}
console.log(
  `Catalog: ${pages.length} routes, ${resources.length} lessons, ${Object.keys(aliases).length} legacy redirects.`,
);
