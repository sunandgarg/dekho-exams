"""Add original practice projects and a decision quiz for offline storage and browser keys."""

import copy
import datetime
import html
import json
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


projects = [
    {
        "path": "web-tech/offline-case-review-upgrade-project",
        "title": "Project: offline case review across upgrades",
        "summary": "Keep unsent inspections readable through worker updates, database upgrades, quota pressure, and account changes.",
        "hub": "web-tech/offline-storage-and-upgrade-safety",
        "intro": "Build a field case-review app for inspector 47, who records evidence while the connection is absent. A draft has a stable local ID, account scope, case ID, server base revision, edit time, and synchronization state. A worker may cache the application shell and public static assets, but it never treats a private case response as shared shell content. The page explains whether each edit exists only on this device, has reached the server, or needs a conflict decision. A queued item is acknowledged only after the server accepts its idempotency key and returns the committed revision. A tab opened on release 24 can finish its edit even when release 25 has installed. The waiting worker asks for a safe activation point; it does not replace a page halfway through an unsent save. The database upgrade uses a versionchange transaction, closes old connections when asked, and explains blocked upgrades to other tabs. Before clearing old records, the app checks that each item has server confirmation and that any promised export is complete. Quota failures stop new offline capture with a visible action path. They do not turn into a false saved indicator. When inspector 47 signs out and inspector 62 signs in, local drafts, caches, and any pending sync handle are scoped and cleared according to policy before the second account can see them.",
        "scope": ["Keep pending drafts readable through a worker activation and database upgrade.", "Show a blocked-tab recovery path without discarding its unsent data.", "Handle quota failure and eviction as ordinary states in the interface.", "Prove one account cannot read another account's offline case content."],
        "code": "function mayActivateRelease(clients) {\n  return clients.every(client => client.pendingWrites === 0 && client.schemaReady);\n}\nconsole.log(mayActivateRelease([{ pendingWrites: 0, schemaReady: true }, { pendingWrites: 2, schemaReady: true }]));\n// Output: false",
        "cost": "An IndexedDB index on account and sync state makes a pending-work query depend on matching records rather than a scan of every case. The worker activation check is O(number of controlled clients), while checking pending records per client depends on its store index. Holding both releases' static assets costs temporary storage. Keep only supported versions and clean old assets after a confirmed transition. Each queued draft consumes bytes until acknowledged; measure local count and estimated usage, but never infer that a browser quota estimate is an exact future guarantee. Exports and server copies cost extra storage and network traffic, which is the price of a genuine recovery path.",
        "failure": "Start an unsent edit in release 24 and install release 25 in another tab. Leave the first tab open, trigger a blocked database upgrade, and confirm the old tab remains readable with a prompt to finish or export its work. Close it and verify the new schema opens before the new worker takes control. Fill storage until an insert fails; the page must report that the new photo is not saved and preserve the prior drafts. Clear site data from browser settings and reopen the app. It should report missing local work honestly and load the last committed server copy. Switch accounts while a sync request is delayed, then deliver the old response and confirm it cannot populate the new account's interface.",
        "checks": ["A pending edit is never described as server saved.", "The old tab closes or exports before a blocked upgrade can complete.", "Quota and eviction paths preserve an honest state report.", "Account switches invalidate stale sync responses and private caches."],
        "mistakes": ["Calling skipWaiting while unsent work belongs to an open client.", "Deleting old stores before verifying migration and sync state.", "Treating a quota estimate as a reservation for future writes."],
        "related": ["web-tech/service-worker-activation-and-unsent-work", "web-tech/indexeddb-versionchange-and-blocked-tabs", "web-tech/browser-storage-quota-eviction-and-recovery", "web-tech/private-offline-cache-and-account-switch"],
    },
    {
        "path": "web-tech/encrypted-local-draft-lifecycle-project",
        "title": "Project: encrypted local draft lifecycle",
        "summary": "Bind private draft ciphertext to its owner and record, then exercise unlock, rotation, backup, and device loss.",
        "hub": "web-tech/browser-cryptography-and-key-custody",
        "intro": "Build an optional local vault for inspector 62's private case drafts. First write a threat model: encrypted bytes may protect stored drafts after a lost device or storage inspection, while code running in an unlocked page can still read plaintext. Keep authentication, record authorization, and server checks separate from the vault. Each record stores a format version, account and record IDs, key version, fresh nonce, ciphertext, and authentication tag. The account and record binding enters authenticated additional data, so swapping the ciphertext between records fails. A password unlock derives a wrapping key using a per-vault salt and a measured work factor, then unwraps the data key; losing the password and recovery material may make offline data unreadable. Never claim that browser storage of an encrypted key grants an independent secret when page code can obtain the key after unlock. A rotation writes a new envelope alongside the old one, verifies that it can decrypt a test record, and only then retires an old envelope under the recovery policy. A server-side session revocation stops future authorized requests but cannot erase an offline copy already held on a lost device. The interface states this boundary before enabling the feature.",
        "scope": ["Reject ciphertext moved to another account or record.", "Never reuse a nonce with the same AES-GCM key.", "Leave a verified recovery route before retiring an old key envelope.", "Explain to users what a lost password or stolen unlocked device means."],
        "code": "function mayRetireEnvelope(rotation) {\n  return rotation.newEnvelopeStored && rotation.decryptVerified && rotation.recoveryConfirmed;\n}\nconsole.log(mayRetireEnvelope({ newEnvelopeStored: true, decryptVerified: false, recoveryConfirmed: true }));\n// Output: false",
        "cost": "Authenticated encryption processes each byte, so encrypting a record takes O(record bytes) time and stores nonce and tag overhead beside ciphertext. Password derivation adds a deliberate unlock delay; measure it on supported low-end devices, because a fixed iteration count is not a universal security setting. Rewrapping a data key is small compared with re-encrypting every draft, but retaining two valid envelopes increases key custody work during rotation. A recovery export needs explicit consent, integrity checks, and a privacy-safe destination. Server synchronization still needs revision and authorization checks, and encrypted content can limit server-side search or inspection if the server cannot decrypt it.",
        "failure": "Encrypt two records with separate nonces. Swap their ciphertext packages and verify authentication fails when account and record IDs are bound to additional data. Corrupt one byte and ensure the app does not replace an existing good draft with partial plaintext. Start rotation and simulate a write failure after the new envelope is stored but before decryption verification. Reopen with the old envelope and keep the record readable. Now lose the password with no recovery key and show the documented loss state rather than inventing a reset. Unlock on a shared computer, inject a script into a controlled test page, and demonstrate that page code can access decrypted material; fix the injection path instead of advertising encryption as script isolation.",
        "checks": ["Tampering and record swaps fail closed without leaking partial data.", "The old envelope remains until the new one and recovery are verified.", "Unlock cost and storage overhead are measured on target devices.", "The threat model separates lost storage from a compromised running page."],
        "mistakes": ["Using a password directly as an AES key.", "Reusing a nonce after an interrupted write or restore.", "Deleting the only readable envelope before a restore drill."],
        "related": ["web-tech/browser-encryption-threat-model-and-key-custody", "web-tech/authenticated-encryption-nonce-and-record-binding", "web-tech/password-unlock-derivation-and-recovery", "web-tech/key-rotation-envelopes-and-device-loss"],
    },
]

for number, project in enumerate(projects, 1):
    assert project["path"] not in by_path
    subprocess.run(["node", "--check", "--input-type=module"], input=project["code"], text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path["web-tech/case-save-incident-evidence-project"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project["path"])), path=project["path"],
                 title=project["title"], summary=project["summary"], sort_order=1270 + number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                     "content_format": "html", "seo_ready": False, "kind": "project",
                     "author_path": "authors/aitrove-editorial", "reading_minutes": 8, "related": project["related"]}
    body = p(project["intro"]) + "<h2>Build contract</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in project["scope"]) + "</ul>"
    body += '<h2>Implementation checkpoint</h2><pre><code class="language-javascript">' + html.escape(project["code"], quote=False) + "</code></pre>"
    body += "<h2>Cost and boundaries</h2>" + p(project["cost"]) + "<h2>Failure drill</h2>" + p(project["failure"])
    body += "<h2>Acceptance checks</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in project["checks"]) + "</ul>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in project["mistakes"]) + "</ul>"
    body += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["related"]) + ".</p>"
    entry["body"] = body
    entries.append(entry)
    by_path[entry["path"]] = entry

questions = [
    ("When may a waiting worker activate during offline editing?", ["At a safe point after controlled clients resolve pending writes", "Whenever its install event completes", "Immediately after one tab paints"], "Activation timing must account for clients that still own unsent work and may rely on the old code or database schema."),
    ("What does an IndexedDB blocked upgrade indicate?", ["Another open connection has not released the old version", "The new schema is already committed", "The server refused the user session"], "A versionchange request waits while old connections remain open; the app should surface a finish, export, or close path."),
    ("What does a browser storage estimate guarantee?", ["No reservation for later writes", "That all drafts persist indefinitely", "That the next write will succeed"], "Estimated usage and quota are advisory snapshots. A write can still fail, and site data can be evicted or cleared."),
    ("What should happen when offline capture hits quota?", ["Report the new item as unsaved and offer a recovery action", "Mark the item saved because it exists in memory", "Delete older pending drafts without review"], "The interface must keep the state honest. A failed local transaction cannot support a saved claim or silent replacement."),
    ("What prevents account 62 seeing account 47's cached case?", ["Account-scoped keys plus cleanup and stale-response rejection", "A shared cache name with a newer timestamp", "A service worker that serves the last successful response"], "Private cache and draft ownership must follow account identity through sign-out, sign-in, delayed requests, and worker lifetime."),
    ("What does browser encryption protect against?", ["Selected storage exposure when keys remain unavailable", "Script executing in the unlocked page", "A server authorization mistake"], "An unlocked page can read its plaintext and usable keys. Encryption does not replace script safety or server permission checks."),
    ("Why bind record IDs as authenticated data?", ["To reject ciphertext moved to a different record", "To make ciphertext shorter", "To avoid storing a nonce"], "Authenticated additional data ties the encrypted package to context without hiding that context; a record swap then fails verification."),
    ("How should a nonce be handled for one AES-GCM key?", ["Use a fresh nonce for each encryption under that key", "Reuse the same nonce after a failed upload", "Derive it from a constant account number"], "Nonce reuse under one key can break the security claim. Persist the chosen nonce with its ciphertext and avoid replaying it for new plaintext."),
    ("What should password unlock derivation include?", ["A per-vault salt and measured work factor", "A raw password copied into the AES key field", "The account ID as the only key material"], "A password needs a suitable derivation process; the salt separates vaults and the work factor must be tested on supported devices."),
    ("What if the vault password and recovery key are both lost?", ["Offline ciphertext may be unrecoverable", "The server can always reset encryption without a key", "A browser restart rebuilds the old key"], "Recovery must be designed before data is stored. Without usable key material, a truthful product cannot promise decryption."),
    ("When can an old wrapping-key envelope be retired?", ["After the new envelope is stored, decrypt-tested, and recovery is confirmed", "Immediately after generating a new key", "When a UI label says rotation complete"], "A rotation is complete only after a readable replacement and recovery route are verified; crashes and quota failures can interrupt it."),
    ("What can server revocation do to an offline lost device?", ["Block future authorized server calls but not erase its existing offline bytes", "Erase local bytes before the device reconnects", "Guarantee that screenshots and copies disappear"], "Remote revocation is a server control. A disconnected device can retain previously stored material until it reconnects and acts."),
]
quiz_path = "quizzes/web-development-offline-crypto-decisions"
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path["quizzes/web-development-graphics-editor-decisions"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: offline and browser-key decisions quiz",
            summary="Twelve explained choices about upgrades, quota, account scope, authenticated encryption, recovery, and rotation.",
            sort_order=1275, created_at=stamp, updated_at=stamp, published_at=stamp)


def quiz_item(number, value):
    prompt, options, explanation = value
    shift = number % 3
    return {"prompt": prompt, "options": options[shift:] + options[:shift],
            "answer": (0 - shift) % 3, "explanation": explanation}


quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes",
                "content_format": "html", "seo_ready": False,
                "questions": [quiz_item(number, value) for number, value in enumerate(questions)]}
quiz["body"] = p(quiz["summary"] + " Choose one answer and inspect the explanation before testing the related contract.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for project in projects for path in project["related"]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path["web-tech/web-technology/project"]
project_hub["data"]["modules"][0]["lessons"].extend(project["path"] for project in projects)
project_hub["body"] += "<h2>Offline and key custody projects</h2><ul>" + "".join(
    "<li>" + link(project["path"]) + " — " + html.escape(project["summary"]) + "</li>" for project in projects) + "</ul>"
project_hub["summary"] = "Build and verify forty-nine projects across browser, API, data, identity, search, rendering, operations, privacy, deployment, offline storage, and key custody."
project_hub["updated_at"] = stamp
quiz_hub = by_path["web-tech/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Offline and key custody checks</h2><p>" + link(quiz_path) + " — " + html.escape(quiz["summary"]) + "</p>"
quiz_hub["updated_at"] = stamp

for project in projects:
    hub = by_path[project["hub"]]
    hub["body"] += "<h2>Practice path</h2><p>Build " + link(project["path"]) + " and check decisions in " + link(quiz_path) + ".</p>"
    hub["updated_at"] = stamp
    for lesson_path in project["related"]:
        lesson = by_path[lesson_path]
        lesson["body"] += "<h2>Connected practice</h2><p>Build " + link(project["path"]) + " and review " + link(quiz_path) + ".</p>"
        lesson["data"]["related"].extend([project["path"], quiz_path])
        lesson["updated_at"] = stamp
root_entry = by_path["web-tech/web-technology"]
root_entry["body"] += "<h2>Offline and key custody practice</h2><p>Apply the tracks with " + link(projects[0]["path"]) + " and " + link(projects[1]["path"]) + ".</p>"
root_entry["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": len(projects), "new_quizzes": 1, "new_questions": len(questions)}))
