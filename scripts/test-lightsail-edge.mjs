import assert from "node:assert/strict";
import { test } from "node:test";
import worker from "../deploy/lightsail/edge.mjs";

import pdfs from "../deploy/lightsail/approved-pdfs.json" with { type: "json" };
const [paper, edition] = Object.entries(pdfs).find(([path, v]) => path.startsWith("/jee-papers/jee-main/") && !v.sha)
  ?? Object.entries(pdfs).find(([,v]) => !v.sha);
test("media requests sign only a public key and preserve partial downloads", async (t) => {
  const saved = globalThis.caches;
  globalThis.caches = { default: { match: async () => undefined } };
  t.after(() => { globalThis.caches = saved; });
  const env = { AWS_REGION: "ap-south-1", MEDIA_BUCKET: "test-dekho", S3_KEY_ID: "test", S3_SECRET: "test" };
  t.mock.method(globalThis, "fetch", async (request) => {
    assert.equal(request.url, "https://test-dekho.s3.ap-south-1.amazonaws.com"+paper);
    assert.match(request.headers.get("authorization"), /^AWS4-HMAC-SHA256 /);
    assert.equal(request.headers.get("range"), "bytes=0-4");
    assert.equal(request.headers.get("cookie"), null);
    return new Response("%PDF-", { status: 206, headers: { "content-range": "bytes 0-4/90", etag:edition.etag } });
  });
  const get = path => worker.fetch(new Request("https://dekhoexams.com" + path, {
    headers: { cookie: "private=1", range: "bytes=0-4" },
  }), env, {});
  const partial = await get(paper);
  assert.equal(partial.status, 206);
  assert.match(partial.headers.get("content-disposition"), /^attachment; filename="DekhoExams-.*\.pdf"$/);
  assert.equal(partial.headers.get("content-range"), "bytes 0-4/90");
  assert.equal(await partial.text(), "%PDF-");
  assert.equal((await get("/jee-papers/private.txt")).status, 404);
  assert.equal(fetch.mock.callCount(), 1);
});

test("origin redirects remain redirects and incoming origin credentials are replaced", async (t) => {
  t.mock.method(globalThis, "fetch", async (url, init) => {
    assert.equal(url.href, "https://origin.example.com/find?q=test");
    assert.equal(init.headers.get("x-origin-key"), "expected");
    assert.equal(init.headers.get("x-dekho-host"), "dekhoexams.com");
    assert.equal(init.redirect, "manual");
    return new Response(null, { status: 308, headers: { location: "/search" } });
  });
  const request = new Request("https://dekhoexams.com/find?q=test", { headers: { "x-origin-key": "forged" } });
  const response = await worker.fetch(request, { APP_ORIGIN: "https://origin.example.com", ORIGIN_KEY: "expected" }, {});
  assert.equal(response.status, 308);
  assert.equal(response.headers.get("location"), "/search");
});

test("shared media and anonymous chapters reuse clean URLs", async (t) => {
  const keys = [];
  t.mock.method(globalThis, "fetch", async () => new Response("private", {headers: {"cache-control":"private"}}));
  const original = globalThis.caches;
  globalThis.caches = {default: {match: async key => {
    keys.push(key.url);
    return new Response("shared");
  }}};
  try {
    const origin = "https://dekhoexams.com";
    const env = { APP_ORIGIN: "https://origin.example.com", ORIGIN_KEY: "test" };
    for (const [path,cookie] of [[paper+"?download=1","session=1"],["/past-years/jee/test?utm_source=test","_ga=1"]]) {
      const response = await worker.fetch(new Request(origin+path,{headers:{cookie}}),env,{});
      assert.equal(response.headers.get("X-Dekhoexams-Cache"), "HIT");
      if (path.endsWith("download=1")) assert.match(response.headers.get("content-disposition"), /^attachment;/);
      const prefix = "/__edge/v25" + (path.startsWith("/jee-papers/") ? "/" + (edition.sha ?? edition.etag) : "");
      assert.equal(keys.at(-1),origin+prefix+path.split("?")[0]);
    }
    for (const [suffix,cookie] of [["?filter=a",""],["","session=1"]]) {
      const response = await worker.fetch(new Request(origin+"/past-years/jee/test"+suffix,{headers:{cookie}}),env,{});
      assert.equal(await response.text(),"private");
    }
  } finally { globalThis.caches = original; }
});

test("unreviewed figures and hidden origin paths are blocked before reading cache", async () => {
  const bad = "/jee-figures/0fe9e9da9d251eaf5355a181.png";
  for (const path of [bad, bad.replace("jee-", "%6aee-"), "/foo%2f..%2f" + bad.slice(1), "/verified-pdf/test.pdf"]) {
    const result = await worker.fetch(new Request("https://dekhoexams.com" + path, {headers:{range:"bytes=0-3"}}), {}, {});
    assert.equal(result.status,404);
  }
});
test("incorrect object versions never reach students", async t => {
  t.mock.method(globalThis,"fetch",async () => new Response(null,{headers:{etag:"changed"}}));
  const result = await worker.fetch(new Request("https://dekhoexams.com"+paper,{method:"HEAD"}), {AWS_REGION:"ap-south-1",MEDIA_BUCKET:"example",S3_KEY_ID:"test",S3_SECRET:"test"}, {});
  assert.equal(result.status,503);
  assert.equal(result.headers.get("Cache-Control"),"no-store");
});

test("S3 HEAD uses a tiny signed GET and returns full object metadata", async t => {
  t.mock.method(globalThis, "fetch", async req => {
    assert.equal(req.method, "GET"); assert.equal(req.headers.get("range"), "bytes=0-0");
    return new Response("%",{status:206,headers:{etag:edition.etag,"content-length":"1","content-range":"bytes 0-0/938"}});
  });
  const result = await worker.fetch(new Request("https://dekhoexams.com"+paper,{method:"HEAD"}),{AWS_REGION:"ap-south-1",MEDIA_BUCKET:"example",S3_KEY_ID:"test",S3_SECRET:"test"},{});
  assert.equal(result.status,200); assert.equal(result.headers.get("content-length"),"938");
  assert.equal(result.headers.get("content-range"),null); assert.equal(result.body,null);
});

test("resuming an older edition restarts the download", async t => {
  t.mock.method(globalThis, "fetch", async req => {
    assert.equal(req.headers.get("range"),null);
    return new Response("%PDF-",{headers:{etag:edition.etag}});
  });
  const r = await worker.fetch(new Request("https://dekhoexams.com"+paper,{headers:{range:"bytes=5-","if-range":'"old-edition"'}}),
    {AWS_REGION:"ap-south-1",MEDIA_BUCKET:"example",S3_KEY_ID:"test",S3_SECRET:"test"}, {});
  assert.equal(r.status,200);assert.equal(await r.text(),"%PDF-");
});
