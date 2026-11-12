import assert from "node:assert/strict";
import { readdir } from "node:fs/promises";
const origin = process.env.TEST_ORIGIN || "http://localhost:3000";
async function check(path, status = 200) {
  const response = await fetch(new URL(path, origin));
  assert.equal(response.status, status, path);
  return response;
}
const chapter = await (await check("/past-years/jee/jee-main/physics/units-and-measurements")).text();
const question = chapter.match(/href="(\/past-years\/jee\/question\/[^"]+)"/);
assert.ok(question, "chapter renders links to real questions");
await check(question[1]);
const papers = "public/jee-papers/jee-main/aieee-2002";
const pdf = (await readdir(papers)).find(file => file.endsWith(".pdf"));
const bytes = Buffer.from(await (await check(papers.slice(6) + "/" + pdf)).arrayBuffer());
assert.equal(bytes.subarray(0,5).toString(), "%PDF-");
await check("/__data/cms-snapshot.txt", 404);
console.log("Verified chapter, question, PDF and private snapshot over HTTP.");
