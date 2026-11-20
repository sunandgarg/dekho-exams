# Student service foundation

The original checkout, profile and payment services remain internal. The private school pilot uses the API described below. The former walkthrough URL `/platform-preview` redirects to `/questions/jee-main/quick-practice`, an anonymous six-question practice set scored in the browser.

The owner-confirmed product is **₹999/month for unlimited mocks**. Public or school coupons grant **one mock** each. A free coupon booking cannot grant a monthly pass. The paid-pass calculation uses one calendar month, clamps month-end and preserves UTC time. This first model does not automatically renew or charge a card.

`schema.sql` is additive and uses `de_` tables. Do not apply it to production before backup/compatibility checks and a versioned migration runner. `checkout.ts` locks student/coupon rows, checks the verified profile phone, scope/expiry/limits and creates one free order/redemption/entitlement atomically. `payments.ts` accepts only a signed captured payment with matching stored order amount/currency and grants/extends a monthly pass idempotently. It does not create Razorpay orders, handle refunds automatically or constitute a complete payment integration. Controllers must authorize the test selection from a server catalog; never trust client-supplied student IDs or prices.

`profiles.ts` provides strict contact, education and optional-birthday saves. Identity verification is separate; typing a contact does not verify it. The active account/guardian checks must happen before a controller calls these functions. `integrations.ts` verifies the explicit owner role and encrypts setting values using AES-256-GCM with a unique nonce and provider/mode binding. The root encryption key belongs only in server secret configuration; it is not stored in MySQL or this repository. Public configuration responses contain field-presence flags, never decrypted credentials. Blank input preserves existing credentials. Saved settings are not represented as connected.

Required next work before launch: session/CSRF middleware, actual Google/OTP drivers and callback configuration, explicit admin bootstrap, guardian verification, rate/spend limits, private attempt snapshots/deadlines, Razorpay order/refund/webhook controllers, SES report worker and delivery tests, authenticated student/admin clients and native apps. See `docs/STUDENT-PLATFORM-PLAN.md` for routes and rollout gates. Do not expose the internal services directly as a generic database API.

Checks:

```sh
npm run test:student
npm run typecheck:student
```

`npm run test:student:db` deliberately connects only to `/tmp/dekhoexams-student-test.sock` as a local isolated test server. It creates a unique throwaway schema and drops it in `finally`. It cannot be pointed at the live database. Tests cover independent profile persistence, coupon retries/global cap races, signed payment replay/month-end, and owner-only encrypted settings. No real email, SMS or gateway call is made.

## Private school pilot

The Node origin now mounts `/api/platform/v1`. Anonymous requests cannot access private records. The pilot runs only with `PLATFORM_ENABLED=true`, the separate `dekhoexams_platform` database, an application user with scoped DML rights over TLS, and a server-held encryption key. The Cloudflare cache does not cache these API or panel routes. SSL and the existing Cloudflare origin authentication remain required.

`provision.mjs` runs the two additive SQL files with a database administration connection on the origin. It creates the runtime configuration with mode 0600 outside the application directory. Use `--owner-link` only on the origin to write a short-lived bootstrap link to a root-only file. Deliver it privately and delete the handoff copy after use. Keep the encryption key in the server secret backup separately from the database. Losing it makes encrypted roster, settings and test results unreadable. This schema has its own database and does not use the archive data account at runtime.

Owner and school access lasts eight hours, student access seven days. Link tokens and session tokens are stored as hashes. School and student activation is one-time and bound to a school or roster account. Students also prove possession of the roster phone with a five-minute MSG91 code. The database limits tries, resend rate and overall daily sends. Roster and settings envelopes use AES-GCM with scoped associated data. Admin/provider fields are write-only in the UI. The school OTP connector requires a live sender key and approved template. Google, payments, SES delivery and native sign-in remain separate work.

The pilot uses an original short diagnostic with server-owned keys and deadlines. Attempts are locked per student and scored at submit or expiry. Reports and award certificates belong to the student who completed the attempt. The report renders the submitted scores and next practice topic as standalone printable HTML without the answer review. School staff get aggregate roster, activation, start and completion counts for their own school. `npm run test:student:db` covers role and tenant authorization, school seats and totals, save revisions, encrypted contact handling, reports and certificates on the local socket.
