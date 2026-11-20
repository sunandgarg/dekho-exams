# Student service foundation

These internal services are not mounted on the live HTTP server. The new public `/platform-preview` is an explicitly labelled design walkthrough with in-memory sample values. It never calls these services, authenticates a user, accepts provider keys or collects a payment. The existing admin editor route remains unchanged.

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
