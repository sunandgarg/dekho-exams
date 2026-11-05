"""Add deep identity, integration, and verification tracks to Web Development."""

import copy
import datetime
import html
import json
import re
import subprocess
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
by_path = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def link(path, label=None):
    assert path in by_path, path
    return f'<a href="/{html.escape(path, quote=True)}">{html.escape(label or by_path[path]["title"])}</a>'


def para(value):
    return f"<p>{html.escape(value)}</p>"


hubs = [
    dict(path="web-tech/identity-and-application-security", title="Identity and Application Security",
         summary="Protect account access, recovery, federated callbacks, and server-side outbound requests.",
         overview="Account security is a chain of independent checks. Password verification establishes one identity claim; a session keeps that claim across requests; recovery can replace it; a federated callback introduces another party; and a server-side fetch can expose internal services if its target is untrusted. Each boundary needs a distinct failure rule and a test that does not depend on the browser hiding controls.",
         bridge=["web-tech/session-cookie-and-csrf-boundary", "web-tech/record-level-authorization", "web-tech/environment-config-and-secrets"]),
    dict(path="web-tech/integration-and-verification", title="Integration and Verification",
         summary="Keep external events, API changes, browser journeys, and performance measurements honest.",
         overview="A working local screen is only one observation. Webhooks cross an untrusted network boundary; API clients outlive one release; browser journeys expose failures invisible to unit tests; and performance measurements vary by device and route. These topics turn integration claims into explicit contracts with failure injection and measured evidence.",
         bridge=["web-tech/contract-tests-across-boundaries", "web-tech/observability-and-recovery", "web-tech/performance-budget-and-layout-stability"]),
]

topics = [
    dict(path="web-tech/password-verification-and-login-budgets", hub=hubs[0]["path"],
         title="Password Verification and Login Budgets",
         summary="Store slow salted verifiers and bound repeated attempts without revealing account existence.",
         definition="Password verification compares a submitted secret with a stored password verifier, not with reversible plaintext. Use a vetted password-hashing facility with a unique salt and a deliberately costly algorithm; keep the algorithm parameters with the stored record so they can be raised later. A successful check establishes identity for this request, after which the server creates or rotates a separate session. The login endpoint must also bound repeated attempts and return similar public feedback for an unknown account and a wrong password. A per-address limit alone can punish a shared office or be bypassed across addresses, so combine account, source, and abuse signals without revealing which account exists. The snippet is one decision boundary; a deployed service should use its platform's maintained password library rather than implementing a hash format by hand.",
         case="Reviewer 29 signs in before editing case 47. The server looks up the account, verifies the submitted password through the configured slow verifier, checks the attempt budget, then issues a fresh session reference. The browser receives a cookie carrying that reference, never the stored verifier. If the account is absent, the response uses the same public wording as a wrong secret. When a password record uses older cost parameters, a successful login can rehash it with current parameters inside a controlled update. None of these steps authorizes access to case 47; record-level permission remains a later request decision.",
         language="javascript", code='''function classifyLoginAttempt({ accountFound, passwordMatches, attemptsRemaining }) {
  if (!attemptsRemaining) return { status: 429, publicMessage: "Try again later" };
  if (!accountFound || !passwordMatches) {
    return { status: 401, publicMessage: "Sign-in details were not accepted" };
  }
  return { status: 200, nextStep: "rotate session identifier" };
}''',
         cost="A password verifier intentionally consumes CPU and often memory for each attempt. That cost slows guessing but can also amplify a denial-of-service attempt if the endpoint has no budget. Account lookup and attempt tracking add storage or shared-counter work; a multi-worker service needs a shared rule. Parameter upgrades may make a successful login slower once, so measure the distribution rather than silently raising costs beyond service capacity. Never log raw passwords, derived hashes, or complete authentication headers; retain only safe outcomes and correlation IDs.",
         failure="A developer stores a fast digest of the password and treats a 401 as enough abuse control. A stolen database can then be tested rapidly offline, while a distributed online attacker continues to guess. Another implementation says 'no account found' for one input and 'wrong password' for another, letting the endpoint enumerate users. Replace the storage method with a maintained slow verifier, keep public responses uniform, and make the budget decision before expensive work where possible without creating a timing leak.",
         checks=["Register two accounts with the same password and confirm their stored verifiers differ because their salts differ.", "Send wrong and nonexistent-account attempts; compare public status and wording without exposing account existence.", "Exhaust the login budget across two app workers and confirm the shared rule still blocks the next attempt."],
         decision="Authentication proves who is making a request; authorization decides which case that person may read. Keep these operations separate in code, tests, and logs so a successful login cannot become blanket permission.",
         mistakes=["Do not store passwords or a fast unsalted digest as the verifier.", "Do not place a password hash or session secret in client-side storage.", "Do not treat a successful login as permission for every record."],
         related=["web-tech/session-cookie-and-csrf-boundary", "web-tech/record-level-authorization", "web-tech/rate-limits-and-request-budgets", "web-tech/environment-config-and-secrets"]),
    dict(path="web-tech/account-recovery-and-session-revocation", hub=hubs[0]["path"],
         title="Account Recovery and Session Revocation",
         summary="Make recovery tokens single-use, short-lived, and separate from an active session.",
         definition="Account recovery is a second route to control an account, so its token is a temporary credential rather than a harmless link. Generate it with a cryptographic random source, store only a protected verifier of the token, bind it to one account and purpose, and expire it after a short documented interval. Consuming the token and changing the password must be one atomic operation; otherwise two requests can use it before either marks it spent. After a successful reset, revoke or rotate existing sessions according to the site's policy and notify the account owner through a separate channel. The request page should give the same public result whether or not an account exists. Do not automatically sign in through the reset response unless the product explicitly designs and protects that session transition.",
         case="A reviewer loses access to the account used for case 47. The recovery request returns a neutral message, then sends a one-use link if the account exists. The link opens a form without revealing the account's private case data. When the reviewer submits a new secret, the server checks token purpose, expiry, and unused state, updates the verifier, marks the token consumed, and invalidates older sessions in the same security workflow. A second click on the original link returns an expired-or-used result. The user can then sign in normally and pass the usual authorization check for case 47.",
         language="sql", code='''UPDATE recovery_tokens
SET used_at = CURRENT_TIMESTAMP
WHERE token_digest = :submitted_digest
  AND purpose = 'password_reset'
  AND used_at IS NULL
  AND expires_at > CURRENT_TIMESTAMP
RETURNING account_id;''',
         cost="Token verification is a bounded lookup when the verifier is indexed; session revocation may touch many active devices for one account. A short expiry reduces exposure but can frustrate people whose delivery is delayed, so the request flow needs a safe way to ask again. Keeping used-token rows briefly helps detect replay without retaining them forever. The SQL statement shows only the claim step: a real reset keeps that claim, password update, and session policy inside one transaction or equivalent atomic workflow.",
         failure="Two reset submissions reach separate workers at almost the same time. Both read an unused token, both update a password, and the last write wins; the account owner cannot tell which secret now works. A second flaw keeps old sessions alive after the reset, so a previously compromised browser remains authorized. Claim the token atomically before accepting a new verifier, reject a second claim, and exercise the session revocation rule as part of the same recovery test.",
         checks=["Request recovery for existing and absent accounts; compare public response wording and status.", "Race two uses of one token and assert that only one password change can commit.", "After reset, replay the old session from another device and verify the documented revocation policy."],
         decision="A recovery token proves control of a narrow recovery channel, not permanent identity. Return the person to a normal sign-in and authorization path after the token is consumed.",
         mistakes=["Do not store a reusable or never-expiring recovery token.", "Do not reveal account existence through the request endpoint.", "Do not forget active sessions when resetting a compromised account."],
         related=["web-tech/password-verification-and-login-budgets", "web-tech/session-cookie-and-csrf-boundary", "web-tech/idempotent-write-requests", "web-tech/transactions-and-concurrent-writes"]),
    dict(path="web-tech/federated-login-callback-boundary", hub=hubs[0]["path"],
         title="Federated Login Callback Boundary",
         summary="Bind an external sign-in response to the browser that began it and verify the identity token.",
         definition="A federated sign-in callback is not a trusted account assertion merely because it contains a code or an email address. The application begins the flow with an unpredictable state value tied to the initiating browser session; a public browser client also uses an authorization-code flow with PKCE. On return, it verifies state, exchanges the code through the registered redirect route, and validates the identity token through a maintained protocol client: issuer, audience, signature, expiry, and nonce where used. Only then does it map the external subject to a local account. Email can change and is not a safe universal key for joining accounts. The short predicate below checks local callback binding only; it intentionally does not parse or verify tokens, which belongs to a vetted protocol implementation.",
         case="Reviewer 29 starts sign-in to open case 47. The server stores a short-lived state and nonce for that browser session, then redirects to the identity provider. An attacker sends the reviewer a callback link from a flow the attacker started elsewhere. The callback's state does not match the pending session and must be rejected before any local account is created. A valid callback still needs code exchange and identity-token verification. After mapping the provider's stable subject to reviewer 29, the application issues its own session and applies case-level permission as usual.",
         language="javascript", code='''import { timingSafeEqual } from "node:crypto";
function acceptCallbackBinding(callbackState, pendingLogin) {
  if (!pendingLogin || pendingLogin.expiresAt <= Date.now()) return false;
  if (typeof callbackState !== "string" || callbackState.length < 24) return false;
  const received = Buffer.from(callbackState);
  const expected = Buffer.from(pendingLogin.state);
  return received.length === expected.length && timingSafeEqual(received, expected);
}''',
         cost="A redirect adds network hops and may depend on an external provider's availability. Pending state and nonce records consume short-lived storage; cleaning them on success and expiry limits replay and memory growth. Token signature verification has CPU cost and key-cache behavior that a maintained client can manage. Repeated callback failures need careful logging without copying codes or tokens into logs. Plan a sign-in outage message that leaves public pages readable rather than turning every route into a blank screen.",
         failure="A callback handler trusts the email value in an unverified token and attaches it to an existing account. The attacker supplies a forged token with the victim's email and gains the victim's case list. Another handler accepts a valid code from a different browser because it never checks state. Both faults cross the identity boundary. Reject a mismatched or expired pending flow, let a maintained client validate protocol tokens, and map accounts by provider and stable subject rather than by display email alone.",
         checks=["Start two login flows in different browser sessions and swap their callbacks; both swaps must fail.", "Reject a token with the wrong issuer, audience, nonce, signature, or expiry in protocol-client tests.", "Change an external account's display email and confirm it does not silently become another local account."],
         decision="Federation delegates credential verification, not local authorization. The application still owns session lifecycle, account mapping, and each protected record decision.",
         mistakes=["Do not trust callback query fields as proof of identity.", "Do not join accounts by an unverified or mutable email alone.", "Do not omit state, PKCE, or identity-token validation from the chosen flow."],
         related=["web-tech/session-cookie-and-csrf-boundary", "web-tech/record-level-authorization", "web-tech/url-origin-and-query-boundary", "web-tech/environment-config-and-secrets"]),
    dict(path="web-tech/outbound-url-and-ssrf-boundary", hub=hubs[0]["path"],
         title="Outbound URL Requests and SSRF Boundaries",
         summary="Keep user-supplied destinations away from private networks and privileged credentials.",
         definition="A server-side fetch has network reach and credentials that a browser visitor does not. If the visitor can choose its destination, the application may become a proxy to internal services, cloud metadata, or another tenant's resource. Treat an outbound URL as untrusted input: decide whether a fixed allowlist is possible, parse the complete URL, restrict schemes and ports, resolve and reject private or special addresses, enforce the rule after redirects and DNS changes, and cap response size and time. Network egress controls provide another boundary. The predicate below is only the first textual allowlist gate, not a complete SSRF defense; a fetch implementation must still enforce DNS and redirect checks at connection time.",
         case="A case editor accepts a URL for a reference photo and the server downloads it to create a thumbnail. An attacker submits a URL pointing at a private administration endpoint reachable only from the server. The response could be stored as an image or leak through error text. A safer design accepts direct file uploads or a small set of approved image hosts. If arbitrary URLs are a true product need, download through a dedicated service with constrained egress, byte and time limits, no ambient privileged headers, and a reviewed redirect policy.",
         language="javascript", code='''function isApprovedImageLocation(candidateUrl) {
  try {
    const target = new URL(candidateUrl);
    const allowedHosts = new Set(["images.inspection.example", "media.inspection.example"]);
    return target.protocol === "https:" && allowedHosts.has(target.hostname)
      && (!target.port || target.port === "443") && !target.username && !target.password;
  } catch {
    return false;
  }
}''',
         cost="DNS lookup, TLS negotiation, download transfer, decoding, and storage all consume resources before a thumbnail exists. A size limit must be enforced while streaming, because a claimed Content-Length may be absent or false. Redirect checks add work per hop, and a strict allowlist adds operational work when an approved provider changes hostnames. Those costs are preferable to granting general network reach to a request controlled by an untrusted user.",
         failure="A filter checks only that the original URL begins with an approved hostname. The server follows a redirect into a private address and sends an internal authentication header along the way. Another attacker uses a hostname whose DNS answer changes between validation and connection. The initial textual check was never sufficient. Bind validation to the actual connection target, disable or revalidate redirects, strip ambient credentials, and restrict network egress so a parsing mistake is not the only defense.",
         checks=["Try a URL with user information, an alternate port, or a deceptive suffix; the textual gate must reject it.", "Redirect from an approved host to a private destination and confirm the connector refuses the hop.", "Stream a response beyond the byte budget and verify the download stops without storing a partial trusted asset."],
         decision="The safest fetch often is no fetch: accept a direct upload or an ID from a known provider. Add general outbound requests only when the product need justifies their ongoing security and operating cost.",
         mistakes=["Do not trust string-prefix URL checks.", "Do not permit redirects or DNS resolution to bypass destination checks.", "Do not forward server credentials to caller-chosen hosts."],
         related=["web-tech/safe-file-upload-pipeline", "web-tech/url-origin-and-query-boundary", "web-tech/environment-config-and-secrets", "web-tech/rate-limits-and-request-budgets"]),
    dict(path="web-tech/signed-webhook-delivery-and-replay", hub=hubs[1]["path"],
         title="Signed Webhook Delivery and Replay Control",
         summary="Verify raw event bytes, reject old deliveries, and process duplicates safely.",
         definition="A webhook is an inbound event sent by another service, usually after the original user request has ended. The receiving endpoint must not trust the JSON body simply because it came to a secret path. Verify a message authentication signature over the exact raw bytes and timestamp with the configured secret, apply the provider's documented timestamp rule, and reject unsupported event types. A correct signature proves the sender possessed a key; it does not prove the event is new or that every referenced record belongs to the local user. Store a stable event ID under a uniqueness constraint before applying side effects, so retries and replay produce one effective result. Keep key rotation and delivery failure handling in the contract.",
         case="An inspection vendor reports that media 61 finished processing for case 47. It sends event 584 with a signature and timestamp. The endpoint verifies the raw payload before JSON parsing, checks that the event is recent, then records event 584 and schedules a bounded case update. The vendor times out and sends the same event again. The second delivery receives a successful acknowledgement but does not attach the image twice. If the event references a case that belongs to another account, the signed origin does not override local record permission or mapping checks.",
         language="javascript", code='''import { createHmac, timingSafeEqual } from "node:crypto";
function hasValidWebhookSignature(rawBody, timestampText, receivedHex, signingKey, nowSeconds) {
  if (!/^\\d+$/.test(timestampText) || !/^[a-f0-9]{64}$/i.test(receivedHex)) return false;
  const sentAt = Number(timestampText);
  if (!Number.isSafeInteger(sentAt) || Math.abs(nowSeconds - sentAt) > 300) return false;
  const signedPayload = Buffer.concat([Buffer.from(`${timestampText}.`), rawBody]);
  const expected = createHmac("sha256", signingKey).update(signedPayload).digest();
  const received = Buffer.from(receivedHex, "hex");
  return received.length === expected.length && timingSafeEqual(received, expected);
}''',
         cost="HMAC verification scans B body bytes in O(B) time before parsing. A uniqueness lookup for event IDs is normally indexed, but deduplication storage grows with the retention window. The receiver should acknowledge quickly and move longer work to a durable queue, creating an at-least-once worker path that also needs safe retries. Timestamp windows are a tradeoff: too wide allows more replay, too narrow rejects delayed but legitimate delivery. Observe delivery age and failure reasons without logging secrets or full private payloads.",
         failure="The handler parses JSON, serializes it again, and signs the reconstructed text. Whitespace and key ordering change, so legitimate events fail. A second version compares signatures with an ordinary early-exit string comparison and does not track event IDs; retries cause duplicate notifications. Verify the original bytes, compare fixed-length digests safely, enforce freshness, and record event identity before the business effect. Do not label the snippet above a complete webhook handler: it shows only the signature comparison step.",
         checks=["Alter one byte of a valid raw payload and require signature rejection.", "Deliver one signed event twice and assert one stored side effect with two safe acknowledgements.", "Send a correctly signed event outside the accepted timestamp window and reject its effect."],
         decision="A signed event is an input to local business rules, not a command that bypasses them. Validate the referenced case and event transition after signature and replay checks.",
         mistakes=["Do not sign parsed and reserialized JSON instead of the raw bytes.", "Do not treat a valid signature as proof that an event is new.", "Do not perform long external work before safely recording the event."],
         related=["web-tech/background-jobs-and-outbox", "web-tech/idempotent-write-requests", "web-tech/record-level-authorization", "web-tech/observability-and-recovery"]),
    dict(path="web-tech/api-evolution-and-compatibility", hub=hubs[1]["path"],
         title="API Evolution and Compatibility Windows",
         summary="Change a response contract without breaking clients that still use the old shape.",
         definition="A deployed API serves clients that do not all upgrade at once. A field rename, status change, or removed enum value can break a browser bundle still cached by a user, even if the server and newest code deploy together. Document which fields are required, which are optional, and how unknown values are handled. Add a new field before removing the old one, dual-read or dual-write during a defined compatibility window, and measure use of the old shape before contracting it. A version number is useful when behavior changes cannot be made compatible, but it does not excuse undocumented breaking changes within a version. Test both old and new clients against the intermediate server state.",
         case="The inspection API returns reviewer_name, while the new interface expects reviewer.displayName. If the server removes reviewer_name in one release, a cached old script renders an empty owner label. An expand step returns both shapes for a short period and records which client shape is requested. A new client reads the nested field and tolerates an absent value until migration completes. After the old bundle's supported lifetime passes and telemetry shows no use, the server can remove the old field in a planned contract step. The same discipline applies to write payloads and error responses.",
         language="javascript", code='''function inspectionOwnerLabel(apiRecord) {
  const modernLabel = apiRecord.reviewer?.displayName;
  if (typeof modernLabel === "string" && modernLabel.trim()) return modernLabel;
  if (typeof apiRecord.reviewer_name === "string") return apiRecord.reviewer_name;
  return "Reviewer unavailable";
}''',
         cost="Temporary fields increase payload size and server branching; dual writes can add storage and reconciliation work. A staged change costs more releases than a direct rename, but it prevents failures in cached browser code, mobile clients, and integrations that upgrade later. Compatibility tests should target the real request/response shapes, not one shared type definition that makes both sides wrong in the same way. Set a measurable removal condition and a support window, or the temporary bridge becomes permanent complexity.",
         failure="The team deploys the new UI and server within minutes, sees green tests, and deletes the old response field. A user who opened the page before deployment keeps the old script in memory and fetches the new response after clicking Next; the page crashes mid-task. Another client sends an old enum value that the new server now rejects. Exercise long-lived browser sessions and old request fixtures before removal. A release is complete only when the compatibility window and exit criteria are explicit.",
         checks=["Run the old browser bundle against the expanded server response and complete a full case read.", "Run the new client against the old and intermediate shapes; confirm its fallback is intentional.", "Remove the old field in staging and make a saved old-client contract test fail before production."],
         decision="Choose compatibility by default for additive changes. Introduce an explicit new version only when the behavior cannot be made compatible without misleading clients, and document how both versions will retire.",
         mistakes=["Do not assume all clients update with the server deploy.", "Do not let a shared mock replace a real compatibility test.", "Do not leave a dual-shape bridge without a removal criterion."],
         related=["web-tech/contract-tests-across-boundaries", "web-tech/expand-and-contract-migrations", "web-tech/cache-etag-revalidation", "web-tech/ci-release-gates"]),
    dict(path="web-tech/browser-journey-and-fault-tests", hub=hubs[1]["path"],
         title="Browser Journey and Fault-Injection Tests",
         summary="Test a user task through navigation, request, response, and visible recovery.",
         definition="A browser journey test verifies an observable task across the actual rendered page, not only a function or mocked handler. Pick a small critical path: open a case directly, submit a note with keyboard controls, see either confirmed storage or a useful failure, and return to the case after refresh. Control test data and network faults so the same test can expose a delayed response, a missing API, or a duplicate retry without waiting for a real outage. Assertions should use semantic roles and visible messages where possible. A green browser journey does not prove every access rule; pair it with server contract and authorization tests. Run against a production-like build for route checks, because a development server may quietly fall back to a client shell for paths production cannot serve.",
         case="The inspection form appears to work in a component test. In the built site, however, a copied /cases/47 URL returns 404; another run submits a valid note but leaves the Save button enabled while the network waits, allowing a duplicate request. A critical journey starts from the direct URL, fills the labeled note field, submits once, waits for a confirmation tied to the stored record, and reloads to verify persistence. A second run intercepts the write with a delay and then a failure, checking that the draft survives and the status tells the person what happened.",
         language="javascript", code='''import { test, expect } from "@playwright/test";
test("case note survives a direct-route refresh", async ({ page }) => {
  await page.goto("/cases/47");
  await page.getByRole("textbox", { name: "Inspection note" }).fill("Seal checked at 09:40");
  await page.getByRole("button", { name: "Save note" }).click();
  await expect(page.getByRole("status")).toContainText("Saved");
  await page.reload();
  await expect(page.getByText("Seal checked at 09:40")).toBeVisible();
});''',
         cost="A browser test starts a full runtime and can make real network and database calls, so it costs more than a unit test. Keep a short critical suite in the release gate and a broader suite on a slower schedule. Explicit waits for a known state are more reliable than fixed sleeps; test retries should not hide a reproducible defect. Isolate test records and clean them safely, or parallel runs will contaminate each other and turn the suite into noise. The snippet is an acceptance target for a project with a functioning case service, not a test claimed to run against the current content-only preview.",
         failure="A test clicks a CSS class, sleeps for one second, and asserts that the button still exists. It passes even when the write failed or a keyboard user could not reach the control. Another test stubs the API with exactly the frontend's assumed response, so a server field rename goes unseen. Assert the meaningful status and persisted result, use semantic selectors, and keep a separate contract check against the real server. Inject one fault at a time so the failing boundary is clear.",
         checks=["Open the nested route as a new visitor without first loading the homepage.", "Delay the write, submit once with the keyboard, and verify the form prevents an accidental duplicate.", "Return an error status and a dropped connection in separate runs; inspect distinct recovery messages."],
         decision="Automate the few journeys whose failure would stop a user from completing a task. Spend human review on unclear copy, focus order, and layout behavior that a locator assertion cannot fully judge.",
         mistakes=["Do not use arbitrary sleeps as the definition of readiness.", "Do not assert only that a button exists after a write.", "Do not let a perfect mock stand in for the server contract."],
         related=["web-tech/contract-tests-across-boundaries", "web-tech/dom-events-progressive-enhancement", "web-tech/accessible-feedback-and-keyboard", "web-tech/release-smoke-and-rollback"]),
    dict(path="web-tech/field-and-lab-performance-evidence", hub=hubs[1]["path"],
         title="Field and Lab Performance Evidence",
         summary="Separate controlled diagnosis from the conditions real visitors experience.",
         definition="A lab run repeats one page under a controlled device and network profile, making a regression easier to reproduce. Field measurements reflect actual visitors, devices, cache states, routes, and interactions. Neither replaces the other. A fast home page says little about a private case route with a large image and active form; one slow trace says little about typical users without distribution and context. Define the task and metric first: useful content, interaction delay, or layout movement. Segment by route and device class, compare the same populations before and after a change, and keep privacy-safe collection. Browser performance APIs can collect timing entries, but support and attribution vary; the code below records navigation timing when available and avoids treating one sample as a site-wide score.",
         case="A release reduces the first page's script bundle but adds a heavy chart to case 47. A lab run of the homepage improves, while reviewers on low-power phones report delayed clicks on the case form. The team needs a case-route lab trace to identify main-thread work and field data to learn how often real reviewers hit it. The page also shifts when a photo loads without a reserved box. Fix the chart work and dimensions, then compare the same route on similar devices; do not claim success from an unrelated route's faster load.",
         language="javascript", code='''function readNavigationTiming(performanceTimeline) {
  const navigation = performanceTimeline.getEntriesByType("navigation")[0];
  if (!navigation) return null;
  return {
    responseMs: Math.round(navigation.responseEnd - navigation.requestStart),
    documentReadyMs: Math.round(navigation.domContentLoadedEventEnd - navigation.startTime)
  };
}''',
         cost="Collecting a few timing values is small local work, but sending every event from every visitor adds transfer, storage, and privacy costs. Sample deliberately and strip account identifiers and private case content. Lab runs cost build and test time; field data takes enough visits to stabilize and can lag behind a release. Large images consume transfer and decoding, while long scripts block interaction even if the response is cached. Diagnose the specific bottleneck before adding more metrics or more client code.",
         failure="The team reports one synthetic score as proof that all case pages are fast. The test used a warm desktop cache and never opened the form, while the affected users have cold mobile loads. Another dashboard averages all routes, hiding a bad inspection page beneath thousands of cheap static guides. Compare distributions for the route and device class that matters, inspect an interaction trace, and state the sample size and observation window before deciding whether a change helped.",
         checks=["Capture cold and warm lab loads for the same case route at a constrained device profile.", "Segment field timing by route and device class instead of averaging the whole site.", "Delay the case photo and inspect both layout movement and the resulting user task path."],
         decision="Use lab traces to explain a suspected cause and field observations to judge impact. A target belongs to a real user task, not to a score detached from the page people use.",
         mistakes=["Do not generalize from one homepage lab run to every route.", "Do not aggregate private case and static guide behavior into one verdict.", "Do not send private content or identifiers with performance telemetry."],
         related=["web-tech/performance-budget-and-layout-stability", "web-tech/browser-parse-load-and-render", "web-tech/image-variants-and-delivery", "web-tech/observability-and-recovery"]),
]

assert len(hubs) == 2 and len(topics) == 8
for hub in hubs:
    assert sum(topic["hub"] == hub["path"] for topic in topics) == 4


def add_entry(path, title, summary, entry_type, section_path, sort_order):
    assert path not in by_path, path
    template_path = "web-tech/getting-started" if entry_type == "article" else "web-tech/web-technology"
    entry = copy.deepcopy(by_path[template_path])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), type=entry_type,
                 path=path, title=title, summary=summary, category="Web Development",
                 subject="web-tech", difficulty="Intermediate" if entry_type == "article" else None,
                 tags=["web-tech", "web-development"], sort_order=1200 + sort_order,
                 status="published", created_at=stamp, updated_at=stamp, published_at=stamp,
                 body="")
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": section_path,
                     "content_format": "html", "seo_ready": False}
    if entry_type == "article":
        entry["data"].update(kind="tutorial", author_path="authors/aitrove-editorial", reading_minutes=8)
    entries.append(entry)
    by_path[path] = entry
    return entry


for number, hub in enumerate(hubs):
    add_entry(hub["path"], hub["title"], hub["summary"], "subject", hub["path"], number)
for number, topic in enumerate(topics):
    add_entry(topic["path"], topic["title"], topic["summary"], "article", topic["hub"], 10 + number)

for topic in topics:
    entry = by_path[topic["path"]]
    code = topic["code"]
    if topic["language"] == "javascript":
        subprocess.run(["node", "--check", "--input-type=module"], input=code, text=True, capture_output=True, check=True)
    body = para(topic["definition"])
    body += "<h2>Working case</h2>" + para(topic["case"])
    body += f'<h2>Implementation boundary</h2><pre><code class="language-{topic["language"]}">' + html.escape(code, quote=False) + '</code></pre>'
    body += "<h2>Cost and boundaries</h2>" + para(topic["cost"])
    body += "<h2>Failure trace</h2>" + para(topic["failure"])
    body += "<h2>Verification</h2><ul>" + "".join(f"<li>{html.escape(check)}</li>" for check in topic["checks"]) + "</ul>"
    body += "<h2>Decision note</h2>" + para(topic["decision"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in topic["mistakes"]) + "</ul>"
    related = [topic["hub"]] + [item["path"] for item in topics if item["hub"] == topic["hub"] and item["path"] != topic["path"]] + topic["related"]
    body += "<h2>Connected lessons</h2><p>" + "; ".join(link(path) for path in related) + ".</p>"
    entry["body"] = body
    entry["data"].update(related=related, reading_minutes=max(6, round(len(re.findall(r"\b\w+\b", re.sub(r"<[^>]+>", " ", body))) / 155)))

for hub in hubs:
    entry = by_path[hub["path"]]
    group = [topic for topic in topics if topic["hub"] == hub["path"]]
    entry["data"]["modules"] = [{"title": hub["title"], "summary": hub["summary"],
                                 "lessons": [topic["path"] for topic in group]}]
    entry["data"]["resource_tabs"] = [
        {"title": "Web Development", "path": "web-tech/web-technology"},
        {"title": "Projects", "path": "web-tech/web-technology/project"},
        {"title": "Quizzes", "path": "web-tech/quizzes"}]
    body = para(hub["overview"])
    body += "<h2>Topics in this track</h2><ul>" + "".join(f'<li>{link(topic["path"])} — {html.escape(topic["summary"])}</li>' for topic in group) + "</ul>"
    body += "<h2>Prerequisite paths</h2><p>" + "; ".join(link(path) for path in hub["bridge"]) + ".</p>"
    body += "<h2>Neighbor track</h2><p>" + link(hubs[0]["path"] if hub == hubs[1] else hubs[1]["path"]) + ".</p>"
    entry["body"] = body

root_entry = by_path["web-tech/web-technology"]
for hub in hubs:
    group = [topic for topic in topics if topic["hub"] == hub["path"]]
    root_entry["data"]["modules"].append({"title": hub["title"], "summary": hub["summary"],
                                         "lessons": [hub["path"]] + [topic["path"] for topic in group]})
    root_entry["body"] += f'<h2>{link(hub["path"])}</h2><p>{html.escape(hub["summary"])}</p><ul>' + "".join(
        f'<li>{link(topic["path"])} — {html.escape(topic["summary"])}</li>' for topic in group) + "</ul>"
root_entry["updated_at"] = stamp

for path, targets in {
    "web-tech/state-and-trust": [hubs[0]["path"]],
    "web-tech/quality-and-release": [hubs[1]["path"]],
    "web-tech/session-cookie-and-csrf-boundary": [topics[0]["path"], topics[1]["path"], topics[2]["path"]],
    "web-tech/safe-file-upload-pipeline": [topics[3]["path"]],
    "web-tech/background-jobs-and-outbox": [topics[4]["path"]],
    "web-tech/contract-tests-across-boundaries": [topics[5]["path"], topics[6]["path"]],
    "web-tech/performance-budget-and-layout-stability": [topics[7]["path"]],
}.items():
    entry = by_path[path]
    entry["body"] += "<h2>Advanced connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": len(hubs), "new_technical_lessons": len(topics),
                  "web_development_routes": sum(entry["path"].startswith("web-tech/") for entry in entries)}))
