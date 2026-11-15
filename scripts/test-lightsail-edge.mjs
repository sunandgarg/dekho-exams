import assert from "node:assert/strict";
import { test } from "node:test";
import worker from "../deploy/lightsail/edge.mjs";

test("media requests sign only a public key and preserve partial downloads", async (t) => {
  const env = { AWS_REGION: "ap-south-1", MEDIA_BUCKET: "test-dekho", S3_KEY_ID: "test", S3_SECRET: "test" };
  t.mock.method(globalThis, "fetch", async (request) => {
    assert.equal(request.url, "https://test-dekho.s3.ap-south-1.amazonaws.com/jee-papers/jee-main/test/en.pdf");
    assert.match(request.headers.get("authorization"), /^AWS4-HMAC-SHA256 /);
    assert.equal(request.headers.get("range"), "bytes=0-4");
    assert.equal(request.headers.get("cookie"), null);
    return new Response("%PDF-", { status: 206, headers: { "content-range": "bytes 0-4/90" } });
  });
  const get = path => worker.fetch(new Request("https://dekhoexams.com" + path, {
    headers: { cookie: "private=1", range: "bytes=0-4" },
  }), env, {});
  const partial = await get("/jee-papers/jee-main/test/en.pdf");
  assert.equal(partial.status, 206);
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
