import assert from "node:assert/strict";
import { readFileSync, readdirSync, writeFileSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import { readyQuestion } from "../src/lib/jee-search.ts";

const origin = "https://dekhoexams.com", seen = new Set();
const data = (name) => JSON.parse(readFileSync("src/data/" + name + ".json", "utf8"));
function write(name, paths) {
  assert(paths.length > 0 && paths.length < 50000);
  for (const p of paths) {
    assert(/^\/[a-zA-Z0-9./-]*$/.test(p) && !seen.has(p), p);
    seen.add(p);
  }
  const xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    paths.sort().map(p => '<url><loc>'+origin+p+'</loc></url>').join('\n') + '\n</urlset>\n';
  assert(Buffer.byteLength(xml) < 50 * 1024 * 1024);
  writeFileSync("public/sitemap-" + name + ".xml", xml);
  console.log(name, paths.length);
}
for (const [exam, folder] of [["jee-main","jee-archive"],["jee-advanced","jee-advanced-archive"]]) {
  const chapters=data(exam+"-chapters"), papers=data(exam+"-papers");
  const hub="/past-years/jee/"+exam,year="/past-years/year-wise/jee/"+exam;
  const paths=[hub,year,"/pyq-pdfs"+year,"/pyq-pdfs"+hub];
  if(exam==="jee-main") paths.push("/");
  for (const [subject, units] of Object.entries(chapters)) {
    for (const path of [hub+"/"+subject,...units.map(c=>hub+"/"+subject+"/"+c)]) paths.push(path,"/pyq-pdfs"+path);
  }
  for (const [subject, chapterSlugs] of Object.entries(chapters)) {
    for (const chapter of chapterSlugs) {
      const rows = JSON.parse(gunzipSync(readFileSync(`public/${folder}/chapter/${subject}/${chapter}.bin`)));
      for (const kind of new Set(rows.map(row => row.group))) paths.push(`${hub}/${subject}/${chapter}/${kind}`);
    }
  }
  write(exam,[...paths,...papers.map(p=>year+"/"+p.slug)]);
  const questions=[];
  for (const shard of readdirSync("public/"+folder+"/q")) {
    const records=JSON.parse(gunzipSync(readFileSync("public/"+folder+"/q/"+shard)));
    for (const q of Object.values(records)) if(readyQuestion(q))
      questions.push(q.chapter ? "/past-years/jee/question/"+q.slug : year+"/"+q.paper+"/"+q.slug);
  }
  write(exam+"-questions",questions);
}

const library = data("published-pdf-collections");
const libraryPaths = ["/pdf-library"];
for (const [exam, entries] of Object.entries(library)) {
  const hub = "/pdf-library/" + exam;
  libraryPaths.push(hub, ...entries.map(entry => hub + "/" + entry.path));
}
write("pdf-library", libraryPaths);
