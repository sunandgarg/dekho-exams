"""Add original offline-lifecycle and browser-cryptography curriculum entries."""

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


def p(value):
    return "<p>" + html.escape(value) + "</p>"


def link(path):
    assert path in by_path, path
    return '<a href="/' + html.escape(path, quote=True) + '">' + html.escape(by_path[path]["title"]) + "</a>"


hubs = [
    {
        "path": "web-tech/offline-storage-and-upgrade-safety",
        "title": "Offline Storage and Upgrade Safety",
        "summary": "Upgrade workers and local data without discarding unsent work or relying on permanent browser storage.",
        "overview": "An offline-capable web app has several independent lifecycles: its page, service worker, local database, cache, and server record. An installable shell can load while its draft store is blocked or gone. This track follows a field inspector who edits cases without a connection and later receives a new app release. It covers waiting worker activation, IndexedDB schema changes, quota and eviction, and account-specific cache cleanup. The server remains the durable authority after synchronization; local state has a visible recovery plan.",
        "bridges": ["web-tech/service-worker-offline-fallback", "web-tech/indexeddb-draft-queue"],
    },
    {
        "path": "web-tech/browser-cryptography-and-key-custody",
        "title": "Browser Cryptography and Key Custody",
        "summary": "Use browser cryptography only with a stated threat model, unique nonces, and a workable key-recovery policy.",
        "overview": "The browser can perform cryptographic operations, but page code and its loaded dependencies execute in the same origin as the protected workflow. Encryption changes who can read stored bytes; it does not replace server authorization, transport protection, or defense against compromised page code. This track follows a local case-note draft that must be unreadable from a copied storage record while its reviewer is signed out. It covers key custody, authenticated encryption, password-based unlock, and rotation. Every design states what happens after device loss, account switch, or key compromise.",
        "bridges": ["web-tech/browser-security-and-data-stewardship", "web-tech/data-retention-export-and-erasure"],
    },
]

topics = [
    {
        "hub": 0,
        "slug": "service-worker-activation-and-unsent-work",
        "title": "Service Worker Activation and Unsent Work",
        "summary": "Coordinate a waiting worker with open pages and unsent drafts before changing the fetch controller.",
        "concept": "A service worker update can install while an older worker still controls open pages. The new worker normally waits until those pages close; an application can request earlier activation, but then a page may run old JavaScript under a new fetch controller. Treat worker activation as a release transition, not a cosmetic refresh. The page owns unsent edits and user attention; the worker owns fetch handling, not a dependable in-memory queue. A safe update path records local draft state before offering a reload and retains assets needed by older tabs.",
        "case": "Inspector 47 is editing case 62 offline when release 29 installs. The active page uses a draft schema that release 29 can still read, but its pending edit has not reached the server. The UI reports that an update is ready and offers a later action. Once the draft transaction commits locally, the inspector can choose to reload. The new worker activates and the page checks which release now controls it before resuming synchronization. If the inspector dismisses the prompt, the old tab remains usable; the deployment retains its hashed assets for that tab.",
        "implementation": "Listen for a waiting worker and state changes on the registration, then separate install success from activation. Record the draft in IndexedDB before acknowledging an update choice. Decide whether to request early activation only when the client and API compatibility window supports mixed versions. On controller change, reload at most once for the selected transition; do not create a loop across worker updates. Keep worker fetch handlers stateless across restarts and store durable outbox entries in the database. A worker can be stopped between events, so a timer or global variable in it is not a reliable retry queue. Keep a server-rendered route available when script or worker registration fails.",
        "cost": "Precache size adds installation transfer and consumes origin storage. Keeping two releases briefly costs extra bytes but protects open tabs from missing chunks. A prompt on every minor release can interrupt field work; group compatible releases and surface the update when the user can act. Pending outbox size should be bounded by records and total bytes. Activation checks are small, while a full reload costs network, parse, and focus restoration. Measure update acceptance, failed chunk loads, unsent draft duration, and the oldest active client release.",
        "failure": "The app calls early activation during an offline edit and immediately deletes every old cache. The old page later imports a lazy module that no longer exists and cannot submit its draft. Simulate this sequence with release 28 open while release 29 installs. Confirm the edit remains in IndexedDB, the old chunk still loads, and the new controller does not mark the server write complete. Test multiple tabs with different releases, a worker installation failure, a browser restart before synchronization, and a user who never chooses to reload. None should silently discard the local change.",
        "drill": "Create a draft generation 47 and a waiting release 29. Before offering reload, commit the generation and count pending outbox entries. Activate the worker only after the selected transition rule passes. Kill the worker process between two simulated events, restart the page, and recover the outbox from storage. Finally, remove an old chunk in staging to show why the asset-retention window must be part of the release contract.",
        "decision": "An update can wait; a field edit must not vanish because the fetch controller changed.",
        "code": "function mayActivateUpdate(draft, compatibility) {\n  return draft.localCommitComplete && (draft.unsentCount === 0 || compatibility.mixedClientSafe);\n}\nconsole.log(mayActivateUpdate({ localCommitComplete: true, unsentCount: 2 }, { mixedClientSafe: false }));\n// Output: false",
        "checks": ["A waiting worker does not clear unsent edits.", "Controller changes cannot trigger reload loops.", "Old open tabs retain their required hashed assets."],
        "mistakes": ["Treating a worker global variable as durable outbox storage.", "Deleting prior assets as soon as a new worker activates.", "Equating local commit with server acknowledgment."],
        "related": ["web-tech/artifact-manifest-rollout-and-rollback-coherence", "web-tech/offline-sync-conflict-policy"],
    },
    {
        "hub": 0,
        "slug": "indexeddb-versionchange-and-blocked-tabs",
        "title": "IndexedDB Version Changes and Blocked Tabs",
        "summary": "Migrate local schema only after older connections release it and preserve queued records across the change.",
        "concept": "An IndexedDB schema upgrade occurs in a version-change transaction. A new database version cannot proceed while older open connections refuse to close. The upgrading page receives a blocked signal; old pages receive a version-change event and should close their connection, save work, and guide the user to reload. Schema changes are local application migrations, not server migrations. Keep records readable across the supported release window and design the upgrade so interruption does not leave an unrecognized outbox.",
        "case": "Release 29 adds a retry timestamp to each queued inspection edit. Tab A opens the new release; Tab B still holds a database connection from release 28 and has an unsent case-62 edit. Tab A waits and explains that another tab must finish or reload. Tab B commits its current transaction, closes its connection on version change, and exposes its pending count before refreshing. Tab A then upgrades the object store. The new application gives old records a default retry timestamp without changing their stable edit IDs or server idempotency keys.",
        "implementation": "Open the database with an explicit version and keep upgrade code synchronous within the version-change transaction; unrelated asynchronous waits can let that transaction become inactive. Use schema operations such as creating stores and indexes only there. Handle the blocked event on the upgrader with a visible retry path. Handle version change on every open connection by stopping new writes, closing the connection, and telling the page to reopen under the supported version. Migrate record fields with a recorded version or read-time normalization where that is safer for large stores. Preserve the outbox's stable IDs. Server writes still validate payloads independently of local schema.",
        "cost": "Scanning n existing drafts during upgrade costs O(n) time and can hold the version-change transaction open. A read-time default reduces one-time migration work but extends compatibility code until old records disappear. An index speeds later queries while consuming extra disk and upgrade time. Keep schema steps narrow and measure the worst populated database on a slow device. Multiple open tabs make upgrade latency visible, so observe blocked duration and the number of unsent records when a user is asked to close a tab.",
        "failure": "Tab B ignores version change and continues to hold the old connection. Tab A displays an endless spinner while the new release assumes the database is ready. Reproduce that blocked upgrade, then verify the UI names the other-tab action and does not send half-migrated edits. Force a browser shutdown midway through a test migration, reopen, and confirm the database is either on the old usable schema or the new complete schema. Test a store with zero records, 47 records, malformed legacy rows, and a full outbox.",
        "drill": "Open two tabs on database version 28. Put one pending case edit in Tab B, then request version 29 in Tab A. Record blocked time and what each tab displays. Close Tab B only after its local transaction finishes. Add the new index and read one old record with a default retry timestamp. Reopen Tab B under version 29 and confirm its edit ID still matches the server idempotency key.",
        "decision": "An upgrade is complete only when every surviving tab agrees on the schema and queued work remains addressable.",
        "code": "function canUpgradeDatabase(connections) {\n  return connections.every(connection => connection.closed || connection.version >= 29);\n}\nconsole.log(canUpgradeDatabase([{ version: 28, closed: true }, { version: 28, closed: false }]));\n// Output: false",
        "checks": ["Older connections close on version change.", "Blocked upgrades show a recoverable user action.", "Queued edit IDs survive migration and restart."],
        "mistakes": ["Waiting on an unrelated network call inside the upgrade transaction.", "Showing an endless loading state for a blocked database.", "Recreating queued edits with new idempotency keys."],
        "related": ["web-tech/indexeddb-draft-queue", "web-tech/cross-tab-invalidation-and-version-checks"],
    },
    {
        "hub": 0,
        "slug": "browser-storage-quota-eviction-and-recovery",
        "title": "Browser Storage Quota, Eviction, and Recovery",
        "summary": "Budget local data, handle failed writes, and give unsent work an export or server path.",
        "concept": "Browser storage is not a permanent disk allocation. IndexedDB, Cache API, and origin-private files can share an origin-level quota; usage estimates are approximate, and the browser may evict best-effort data under storage pressure or after user action. A persistence request may lower eviction risk where granted but cannot protect against explicit clearing or device loss. Treat local drafts as recoverable state with a visible synchronization or export plan. Never claim a successful UI save before the storage transaction finishes.",
        "case": "Inspector 47 captures 29 high-resolution scans while offline. The cached display copies and the unsent case notes compete for the same origin storage. The app keeps compact thumbnails, bounds the attachment queue, and warns before taking another large scan. If a write fails with a quota error, it retains the current form values in memory long enough to offer retry, smaller file selection, or an encrypted export chosen by the user. Once online, the app uploads and verifies the server copy before deleting an unsent local source. A fresh install with empty storage starts from server state instead of assuming a prior cache exists.",
        "implementation": "Use storage estimates to guide a budget, not as a guaranteed reservation. Record byte counts for queued attachments and drafts, cap the queue, and evict regenerable thumbnails before unsent user data. Wrap each local write in an error path and wait for its transaction completion. Request persistent storage only if the product can explain why it needs it; handle denial. An export must include version and integrity metadata and be tested through restore. On startup, distinguish empty cache from an unsent queue and from corrupt local records. The server acknowledges uploaded bytes and record version before the client marks an item safe to remove.",
        "cost": "Large binary records consume disk, serialization time, and memory during readback. If n scans average s bytes, queued storage is O(n times s), excluding thumbnails and duplicate temporary buffers. Storage estimates can be padded for privacy and vary by browser, so leave headroom rather than filling to a reported limit. Clearing thumbnails costs extra downloads later; losing an unsent report costs far more. Track quota failures, queue bytes, age of oldest unsent item, restore success, and the fraction of users denied persistence without recording document contents.",
        "failure": "The app labels an attachment saved immediately after calling a write method, then the transaction aborts for quota. The inspector closes the tab and loses the only copy. Reproduce an abort after the UI starts a save and verify the status remains unsaved until completion. Simulate origin eviction between sessions, private-browsing cleanup, a user clearing site data, and a partial export file. The startup flow must tell the difference between no local work and missing local work; a server sync check can recover acknowledged records, while an unacknowledged draft needs a separately tested export path.",
        "drill": "Fill a test origin near its usable storage budget with 29 scans. Attempt one more write, catch the failure, discard only regenerable thumbnails, and retry the record transaction. Export an unsent report, clear site data, and restore it into a fresh profile. Compare restored record IDs and revision markers with the original queue. Then reconnect and verify the server acknowledgment before deleting local bytes.",
        "decision": "Local storage improves continuity; verified server state or a tested export protects against its loss.",
        "code": "function nextStorageAction(queuedBytes, budgetBytes, newScanBytes) {\n  return queuedBytes + newScanBytes > budgetBytes ? 'offer-smaller-file-or-export' : 'attempt-transaction';\n}\nconsole.log(nextStorageAction(47_000_000, 62_000_000, 29_000_000));\n// Output: offer-smaller-file-or-export",
        "checks": ["Write status waits for transaction completion.", "Quota failure preserves a user-visible recovery path.", "Server acknowledgment precedes local source deletion."],
        "mistakes": ["Treating an estimated quota as reserved capacity.", "Deleting unsent user data before regenerable cache entries.", "Assuming a granted persistence request survives explicit clearing."],
        "related": ["web-tech/file-ingestion-and-private-asset-lifecycle", "web-tech/offline-sync-conflict-policy"],
    },
    {
        "hub": 0,
        "slug": "private-offline-cache-and-account-switch",
        "title": "Private Offline Cache and Account Switch",
        "summary": "Keep account-scoped drafts and responses apart, then clear every local view on identity change.",
        "concept": "A service worker intercepts requests by scope, not by a user's server authorization. Cache API entries and IndexedDB rows can remain on a shared device after logout unless the application removes them. A cache name containing an account ID is an organization aid, not a security boundary; same-origin scripts can inspect origin storage. Decide which private data may be stored locally at all, minimize it, and enforce server authorization for every network response. Account switch must invalidate open views and pending work as well as remove local bytes.",
        "case": "Reviewer 47 reads a private case summary offline, then signs out and lends the device to reviewer 62. The application clears its in-memory case model, terminates file previews, closes database connections, removes account-47 cache and draft partitions, and refuses to replay account-47 mutations under the new session. Reviewer 62 opens a fresh signed-in session and sees only authorized server data. A delayed response from the former account is discarded by an identity generation check. The logout UI does not claim the browser erased data already copied into screenshots or another process.",
        "implementation": "Treat cache writes as explicit opt-in by response type. Never put private authenticated responses into a shared shell cache with a broad URL-only key. Include an account or session generation in local record metadata and verify it before display or replay. On logout or account switch, stop fetches, revoke object URLs, close database handles, delete owned Cache API entries and draft rows, and reset visible state before the next account renders. Coordinate open tabs with a generation message, but assume a crashed tab may miss it and recheck on resume. Keep authorization on the server even if the offline view has already hidden a record.",
        "cost": "Account partitioning adds storage and cleanup work; duplicated shell assets should remain public and shared only when they carry no private response. Deleting many draft rows can be O(n), so show cleanup progress for a large queue and block new-account display until isolation is complete. Late network responses need a generation comparison at their application boundary. Test memory, object URLs, Cache API, IndexedDB, and open tabs. Avoid recording private case titles in cleanup telemetry; counts and failure categories are enough for operations.",
        "failure": "The worker caches a case response under its URL and serves it after the browser receives a different account cookie. Another tab misses the logout event and replays a mutation from reviewer 47 while reviewer 62 is signed in. Reproduce both cases. The cache must refuse an account mismatch, and outbox records must carry an owner identity that is checked before replay. Also test a failed cleanup transaction, interrupted logout, back navigation, and a delayed fetch. The UI should block private content rather than show stale data during recovery.",
        "drill": "Populate two private case summaries and one pending edit for reviewer 47. Switch to reviewer 62 in another tab, then resume the first tab from sleep. Confirm every display and replay checks the current identity generation. Inspect Cache API, IndexedDB, in-memory state, and object URLs after cleanup. Cause deletion to fail once and verify the new account cannot view or use the prior account's data while cleanup is incomplete.",
        "decision": "Account separation requires server checks plus explicit browser cleanup and generation gates on delayed work.",
        "code": "function mayReplayOfflineEdit(edit, session) {\n  return edit.ownerId === session.userId && edit.identityGeneration === session.generation;\n}\nconsole.log(mayReplayOfflineEdit({ ownerId: 47, identityGeneration: 6 }, { userId: 62, generation: 7 }));\n// Output: false",
        "checks": ["Private responses never enter a public shell cache.", "Late replies and queued edits check identity generation.", "Open tabs clear prior-account views before rendering a new account."],
        "mistakes": ["Treating a cache name as isolation from same-origin scripts.", "Clearing only visible React state while retaining private Cache API entries.", "Replaying old-account writes with a new account cookie."],
        "related": ["web-tech/browser-storage-cleanup-on-account-change", "web-tech/tenant-scope-in-cache-and-background-work"],
    },
    {
        "hub": 1,
        "slug": "browser-encryption-threat-model-and-key-custody",
        "title": "Browser Encryption Threat Model and Key Custody",
        "summary": "Decide what copied storage bytes should resist and who can still use the decryption key.",
        "concept": "Browser encryption protects a defined data boundary, not every part of a web app. A non-extractable CryptoKey cannot be exported through the normal API, but page code with access to that key may still ask the browser to decrypt. A cross-site scripting flaw can operate inside the same origin and misuse the key or read plaintext after unlock. State the adversary: copied browser storage, a lost device profile, an untrusted server, or compromised running code require different designs. Keep server credentials and authorization decisions off the client.",
        "case": "Reviewer 47 keeps a short case-note draft on a shared tablet. The product wants a copied IndexedDB record to reveal no note text after the reviewer signs out. The draft is encrypted before storage, and the unlock key is not persisted in readable form beside it. The account session still controls whether the server accepts a save. If the reviewer loses the unlock secret and no recovery key exists, the local-only draft cannot be restored; the UI states that cost before offline work begins. An attacker who can run script in the unlocked page remains within the threat model's limits.",
        "implementation": "Start with a data-flow diagram: where plaintext enters, where a key originates, when it is available, what persists, and what is deleted on logout. Use the platform cryptography API rather than custom primitives. Define key usages narrowly and keep an encryption key separate from a signing or authentication purpose. Store an envelope with algorithm, version, key ID, nonce, and ciphertext, while never treating this metadata as secret. A non-extractable browser key may be stored as a CryptoKey object, but that does not make it inaccessible to every script in the origin. Use a stronger external unlock factor when the copied-profile threat requires it; test device loss and recovery before enabling offline drafting.",
        "cost": "Encryption adds CPU work proportional to message size, extra nonce and tag bytes, and key-management flows that can be harder than the cipher call. For a 47-kilobyte note, the cryptographic operation may be cheap while unlock, backup, account switch, and support costs dominate. Avoid repeated encryption of unchanged content. Keep plaintext lifetime short in memory, but do not promise JavaScript can reliably zero every browser copy. Record only envelope version and error category in telemetry. A key-custody design that support staff cannot recover must be presented as such.",
        "failure": "The app generates a non-extractable key and stores it next to ciphertext in IndexedDB. After logout, an injected same-origin script reads the key object and invokes decrypt; the property did not prevent use. Another build clears the key on logout but has no recovery path for unsent drafts after a browser crash. Rehearse copied storage, compromised unlocked page, device loss, browser-site-data clearing, and account switch as separate tests. Document which threat is reduced and which remains. If the server must search note contents, explain how browser-only encryption changes that feature.",
        "drill": "List every component that sees note plaintext or a usable key during case 62 editing. Decide whether the design targets copied storage or a server that must never see the note. Unlock and save a draft, then sign out and attempt to read its stored bytes without the factor. Simulate a malicious same-origin script during the unlocked session and record the remaining exposure. Lose the device profile and execute the stated recovery or data-loss path.",
        "decision": "Choose key custody from the threat model and recovery contract, not from the availability of an encryption API.",
        "code": "function copiedStorageProtected(envelope, keyCustody) {\n  return envelope.encrypted === true && keyCustody.usableKeyStoredBesideEnvelope === false;\n}\nconsole.log(copiedStorageProtected({ encrypted: true }, { usableKeyStoredBesideEnvelope: true }));\n// Output: false",
        "checks": ["The design names the attacker it resists.", "A usable key is not stored unprotected beside ciphertext.", "Device-loss and unlock-secret-loss behavior is documented."],
        "mistakes": ["Calling non-extractable a guarantee against same-origin script misuse.", "Treating browser encryption as server authorization.", "Offering offline-only drafts without a recovery decision."],
        "related": ["web-tech/dom-sinks-and-trusted-content", "web-tech/browser-storage-cleanup-on-account-change"],
    },
    {
        "hub": 1,
        "slug": "authenticated-encryption-nonce-and-record-binding",
        "title": "Authenticated Encryption, Nonce, and Record Binding",
        "summary": "Encrypt a draft with a fresh nonce and bind its ciphertext to the intended record metadata.",
        "concept": "Authenticated encryption returns ciphertext with an integrity check. With AES-GCM, the nonce must be unique for every encryption under one key; repeating it can break confidentiality and integrity. A 96-bit random nonce is a common choice for modest volumes, with a rekey and volume limit set by policy. Additional authenticated data can bind the ciphertext to a record ID, owner, and envelope version without hiding those fields. The decrypting side must reconstruct the same bytes exactly, then reject a failed authentication tag rather than showing partial plaintext.",
        "case": "Case 62 has note revision 29 owned by reviewer 47. The browser encrypts its UTF-8 note with a fresh 12-byte nonce, and authenticated metadata identifies case 62, reviewer 47, and schema version 3. A copied ciphertext moved under case 63 fails to authenticate because the record binding differs. A changed tag also fails. The server may store the envelope but still checks the session and object permission on upload and download. If the app cannot unlock or authenticate the note, it keeps the original envelope for recovery rather than overwriting it with an empty draft.",
        "implementation": "Generate the nonce using a cryptographically secure random source for each encryption, never a timestamp or Math.random. Persist it with the ciphertext. Encode authenticated metadata in a stable canonical representation; changing field order or text encoding breaks decryption. Fix a key ID and envelope version so a later rotation can select the right key. Catch decryption rejection and present a corrupt-or-wrong-key state without exposing decrypted fragments. Bound note size and encrypt on save rather than every keystroke. Test with a known approved implementation before shipping; a demo that round-trips once does not establish safe nonce management over years.",
        "cost": "Encryption work is O(n) in plaintext bytes and creates at least one additional buffer. A nonce and authentication tag add fixed overhead per note. If many tiny records use one key, nonce-collision risk grows with operation count; the product must cap use or choose a coordinated scheme and rotate before its bound. Canonical metadata serialization also costs O(metadata size). Avoid logging plaintext, keys, or full envelopes. Measure save latency for realistic note sizes and verify the app can stop an oversized write before allocating several full copies.",
        "failure": "A developer derives a nonce from case ID so revision 29 and revision 30 reuse it with the same key. A second implementation encodes authenticated metadata in a different order and can no longer read old drafts. Simulate both cases. Tamper with one ciphertext byte, swap envelopes between cases, change the owner ID, and try the wrong key. Every unauthorized or corrupt attempt must fail authentication. On failure, the app should retain the original bytes, show a recoverable error, and avoid silently generating a replacement note that could later synchronize as a deletion.",
        "drill": "Encrypt a 47-kilobyte case note twice under one key and confirm the nonce bytes differ. Decrypt with matching record metadata, then alter the case ID and verify authentication fails. Restart the app and decode the stored envelope using its declared version. Count how many encryptions one key can perform under the chosen nonce policy and define when the key rotates before reaching that bound.",
        "decision": "The envelope carries enough versioned context to reject swapped or altered records without confusing failure with an empty note.",
        "code": "const caseKey = await crypto.subtle.generateKey({ name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']);\nconst noteBytes = new TextEncoder().encode('Case 62: seal split at region 29');\nconst nonce = crypto.getRandomValues(new Uint8Array(12));\nconst recordBinding = new TextEncoder().encode('case=62;owner=47;schema=3');\nconst sealedNote = await crypto.subtle.encrypt({ name: 'AES-GCM', iv: nonce, additionalData: recordBinding }, caseKey, noteBytes);\nconst openedNote = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: nonce, additionalData: recordBinding }, caseKey, sealedNote);\nconsole.log(new TextDecoder().decode(openedNote) === 'Case 62: seal split at region 29');\n// Output: true",
        "checks": ["Every encryption under a key uses a unique nonce.", "Changing bound case or owner metadata fails authentication.", "A failed decrypt never becomes an empty saved note."],
        "mistakes": ["Reusing an ID-derived nonce with the same key.", "Omitting envelope version and key ID.", "Treating an authentication failure as missing content."],
        "related": ["web-tech/record-level-authorization", "web-tech/undo-history-autosave-and-revision-conflicts"],
    },
    {
        "hub": 1,
        "slug": "password-unlock-derivation-and-recovery",
        "title": "Password Unlock, Derivation, and Recovery",
        "summary": "Derive an unlock key with recorded parameters and make forgotten-secret behavior explicit.",
        "concept": "A human password is not a high-entropy encryption key. A password-based key derivation function uses a per-envelope random salt and a calibrated work factor to make guessing more expensive. The salt is stored openly with the envelope; it is not a second password. A derived unlock key may wrap a random data-encryption key so the user's password can change without re-encrypting every document. This design still depends on password strength, device performance, and a recovery policy. It should never be confused with server-side password hashing for authentication.",
        "case": "Reviewer 47 unlocks offline notes on a shared tablet with a passphrase. The app generates a random data key for the draft collection and wraps it under a key derived from that passphrase, a 16-byte salt, and versioned derivation parameters. The server stores only the encrypted envelope for this workflow. If the reviewer changes the passphrase, the app rewraps the data key after successful unlock. If the reviewer forgets the passphrase and has no recovery factor, the notes remain unreadable; a normal account password reset cannot decrypt them by itself.",
        "implementation": "Choose a supported password KDF and calibrate its work factor on target devices, recording algorithm, salt, iteration count, and version beside the wrapped key. Web Crypto supports PBKDF2; a product may use a carefully reviewed stronger password-hardening scheme through a maintained implementation if its deployment supports it. Generate salts with a secure random source and never reuse a fixed salt for every reviewer. Derive an unlock key in a secure context, unwrap only the needed data key, and clear references on logout as far as the application can. Require a deliberate recovery or no-recovery decision before storing sole-copy drafts. A server authentication password should not silently become the local encryption secret.",
        "cost": "A higher KDF work factor slows offline guessing but also delays every legitimate unlock. Derive once per unlock session, not per keystroke or per record. Store wrapped data keys so a passphrase change costs O(number of keys), not O(total note bytes), if the threat model permits that structure. Browser memory can still contain passphrase strings or decrypted notes beyond an application's precise control. Measure unlock time on low-end devices and document support costs for forgotten secrets. Avoid logging salts with user identifiers when that metadata is unnecessary for operations.",
        "failure": "The app raises its KDF iteration count in release 29 but fails to record the old value with existing envelopes. After upgrade, every old draft appears corrupt. Another build resets the account password and tells the reviewer local encrypted notes are restored, although the old unwrap secret is gone. Reproduce both cases. Test wrong passphrase, corrupted wrapped key, missing salt, outdated parameters, browser restart during rewrap, and a device with low memory. Preserve the original envelope until the new wrapping is fully verified.",
        "drill": "Create a collection key for 29 local notes and wrap it under derivation version 3. Change the passphrase and produce a new wrap without rewriting the note ciphertext. Verify the old passphrase no longer unlocks the new wrap after the change is committed, while an interrupted change can still restore the old envelope. Simulate a forgotten passphrase and show the user the stated recovery or permanent-loss path before accepting more offline-only work.",
        "decision": "A password unlock is a versioned key-custody system with measurable delay and an explicit loss policy.",
        "code": "function canUnlockEnvelope(envelope, supportedVersions) {\n  return envelope.saltBytes >= 16 && envelope.iterations > 0 && supportedVersions.has(envelope.kdfVersion);\n}\nconsole.log(canUnlockEnvelope({ saltBytes: 16, iterations: 240000, kdfVersion: 3 }, new Set([2, 3])));\n// Output: true",
        "checks": ["Each envelope records its KDF parameters.", "Password reset does not claim to recover unavailable local keys.", "Interrupted rewrap retains a readable previous envelope."],
        "mistakes": ["Using a fixed salt for every account.", "Changing derivation cost without versioning old envelopes.", "Deriving a key for every note when a wrapped collection key suffices."],
        "related": ["web-tech/passkey-management-recovery-and-step-up", "web-tech/data-retention-export-and-erasure"],
    },
    {
        "hub": 1,
        "slug": "key-rotation-envelopes-and-device-loss",
        "title": "Key Rotation, Envelopes, and Device Loss",
        "summary": "Re-encrypt local records under a new key without losing drafts or overstating revocation.",
        "concept": "Key rotation changes which key encrypts future data and, when required, migrates existing envelopes. Each stored record needs a key ID and format version so readers can select the correct key during a transition. A rotation is not complete merely because a new key was generated; old ciphertext, offline devices, backups, and exports still exist. Revoking a key can stop a cooperative app from decrypting new downloads, but it cannot erase plaintext or ciphertext already copied elsewhere. Define the supported device and backup window before changing keys.",
        "case": "Reviewer 47 reports a lost tablet that held encrypted drafts for case 62. The server revokes that device session and future synchronization, while the team assesses whether its browser key was protected by a separate unlock factor. On another device, release 29 creates key version 4 for new drafts. Existing local envelopes tagged version 3 remain readable during a controlled migration. The application writes a version-4 envelope and verifies decrypt before deleting the version-3 local copy. The incident record does not promise deletion from the lost tablet, because it may never reconnect.",
        "implementation": "Store algorithm, envelope version, key ID, nonce, and authenticated record metadata with each ciphertext. Maintain a narrow reader window for old key IDs while re-encrypting in batches. Write the new envelope first, verify it under the new key, then atomically mark the migration complete for that record where storage permits. Pause synchronization of a record whose migration state is uncertain. Keep a backup or export recovery plan for key loss, subject to the chosen privacy model. On account switch, remove usable key references and local plaintext, but keep server authorization as the decisive barrier to future records. Audit key issuance, rotation, and retirement without logging key material.",
        "cost": "Re-encrypting n records of total size b takes O(b) cryptographic work and can temporarily require close to twice the local bytes. On a nearly full device, rotation may fail due to quota even though normal edits still fit. Batch work and expose progress, cancellation, and resume state. Retaining old keys extends exposure, so set a retirement deadline tied to observed migration and backup policy. A lost offline device may never acknowledge rotation; device revocation should stop server access while the product explains the limit of local deletion.",
        "failure": "The app overwrites a version-3 envelope with a version-4 ciphertext before verifying that the new key can read it. A crash leaves the only draft unreadable. Reproduce a crash between write and verification, a full-storage error during rotation, a missing old key, and two devices on different releases. The migration must preserve a readable old copy until success, then retire it according to policy. Simulate a lost tablet staying offline forever; the server must deny future writes from its revoked session without claiming it erased local bytes.",
        "drill": "Create 47 encrypted draft envelopes tagged key version 3. Rotate a few to version 4, interrupt the process, and resume without duplicating or dropping a record. Force a quota failure and show the user which records remain on version 3. Revoke a lost device and attempt server replay with its old session. Inspect the rotation audit: it should name key IDs, counts, and outcomes, never raw key bytes or note text.",
        "decision": "Rotation is a verified data migration plus access revocation; neither operation can undo a prior copy.",
        "code": "function mayDiscardOldEnvelope(rotation) {\n  return rotation.newEnvelopeWritten && rotation.newEnvelopeVerified && rotation.backupPolicySatisfied;\n}\nconsole.log(mayDiscardOldEnvelope({ newEnvelopeWritten: true, newEnvelopeVerified: false, backupPolicySatisfied: true }));\n// Output: false",
        "checks": ["Every envelope names the key version needed to read it.", "A crash or quota failure leaves a readable old copy.", "Revoked device sessions cannot replay to the server."],
        "mistakes": ["Generating a new key and calling old data rotated.", "Deleting the only readable ciphertext before verification.", "Promising remote erasure from a device that stays offline."],
        "related": ["web-tech/backup-restore-with-deletion-tombstones", "web-tech/browser-storage-cleanup-on-account-change"],
    },
]

assert len(hubs) == 2 and len(topics) == 8
for number, hub in enumerate(hubs):
    path = hub["path"]
    assert path not in by_path
    entry = copy.deepcopy(by_path["web-tech/production-signals-and-incident-decisions"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                 title=hub["title"], summary=hub["summary"], sort_order=2970 + number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": path,
                     "content_format": "html", "seo_ready": False, "modules": [],
                     "resource_tabs": [{"title": "Web Development", "path": "web-tech/web-technology"},
                                       {"title": "Projects", "path": "web-tech/web-technology/project"},
                                       {"title": "Quizzes", "path": "web-tech/quizzes"}]}
    entries.append(entry)
    by_path[path] = entry

for number, topic in enumerate(topics):
    path = "web-tech/" + topic["slug"]
    assert path not in by_path
    subprocess.run(["node", "--check", "--input-type=module"], input=topic["code"],
                   text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path["web-tech/trace-context-across-request-and-job"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                 title=topic["title"], summary=topic["summary"], sort_order=2980 + number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    hub_path = hubs[topic["hub"]]["path"]
    related = [hub_path] + ["web-tech/" + item["slug"] for item in topics
                            if item["hub"] == topic["hub"] and item["slug"] != topic["slug"]] + topic["related"]
    body = p(topic["concept"]) + "<h2>Working case</h2>" + p(topic["case"])
    body += '<h2>Implementation boundary</h2><pre><code class="language-javascript">' + html.escape(topic["code"], quote=False) + "</code></pre>" + p(topic["implementation"])
    body += "<h2>Cost and boundaries</h2>" + p(topic["cost"]) + "<h2>Failure trace</h2>" + p(topic["failure"])
    body += "<h2>Verification</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in topic["checks"]) + "</ul>"
    body += "<h2>Practice drill</h2>" + p(topic["drill"]) + "<h2>Decision note</h2>" + p(topic["decision"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in topic["mistakes"]) + "</ul>"
    entry["body"] = body
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": hub_path,
                     "content_format": "html", "seo_ready": False, "kind": "tutorial",
                     "author_path": "authors/aitrove-editorial", "reading_minutes": 7, "related": related}
    entries.append(entry)
    by_path[path] = entry

for topic in topics:
    entry = by_path["web-tech/" + topic["slug"]]
    entry["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(target) for target in entry["data"]["related"]) + ".</p>"

for number, hub in enumerate(hubs):
    group = [item for item in topics if item["hub"] == number]
    entry = by_path[hub["path"]]
    entry["data"]["modules"] = [{"title": hub["title"], "summary": hub["summary"],
                                  "lessons": ["web-tech/" + item["slug"] for item in group]}]
    entry["body"] = p(hub["overview"]) + "<h2>Topics in this track</h2><ul>" + "".join(
        "<li>" + link("web-tech/" + item["slug"]) + " — " + html.escape(item["summary"]) + "</li>" for item in group) + "</ul>"
    entry["body"] += "<h2>Prerequisite paths</h2><p>" + "; ".join(link(path) for path in hub["bridges"]) + ".</p>"
    entry["body"] += "<h2>Neighbor track</h2><p>" + link(hubs[1 - number]["path"]) + ".</p>"

root_entry = by_path["web-tech/web-technology"]
for number, hub in enumerate(hubs):
    group = [item for item in topics if item["hub"] == number]
    root_entry["data"]["modules"].append({"title": hub["title"], "summary": hub["summary"],
                                           "lessons": [hub["path"]] + ["web-tech/" + item["slug"] for item in group]})
    root_entry["body"] += "<h2>" + link(hub["path"]) + "</h2>" + p(hub["summary"]) + "<ul>" + "".join(
        "<li>" + link("web-tech/" + item["slug"]) + " — " + html.escape(item["summary"]) + "</li>" for item in group) + "</ul>"
root_entry["updated_at"] = stamp

crosslinks = {
    "web-tech/service-worker-offline-fallback": [hubs[0]["path"], "web-tech/service-worker-activation-and-unsent-work"],
    "web-tech/indexeddb-draft-queue": ["web-tech/indexeddb-versionchange-and-blocked-tabs", "web-tech/browser-storage-quota-eviction-and-recovery"],
    "web-tech/offline-sync-conflict-policy": ["web-tech/private-offline-cache-and-account-switch"],
    "web-tech/browser-storage-cleanup-on-account-change": ["web-tech/private-offline-cache-and-account-switch", hubs[1]["path"]],
    "web-tech/dom-sinks-and-trusted-content": ["web-tech/browser-encryption-threat-model-and-key-custody"],
    "web-tech/file-ingestion-and-private-asset-lifecycle": ["web-tech/browser-storage-quota-eviction-and-recovery"],
    "web-tech/record-level-authorization": ["web-tech/authenticated-encryption-nonce-and-record-binding"],
    "web-tech/backup-restore-with-deletion-tombstones": ["web-tech/key-rotation-envelopes-and-device-loss"],
}
for path, targets in crosslinks.items():
    entry = by_path[path]
    entry["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": len(hubs), "new_lessons": len(topics),
                  "prose_words": {topic["slug"]: len(re.findall(r"\b[\w'-]+\b", " ".join(str(value) for key, value in topic.items() if key not in {"code", "checks", "mistakes", "related"}))) for topic in topics}}))
