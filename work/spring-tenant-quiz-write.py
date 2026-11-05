"""Extend the Spring web/security quiz with checked tenant JWT cases."""
from __future__ import annotations

import datetime
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILE = ROOT / "src/data/fixtures.json"
rows = json.loads(FILE.read_text())
quiz = next(row for row in rows if row["path"] == "quizzes/spring-web-security")
by_path = {row["path"]: row for row in rows}
questions = [
    ("A signed receipt.read token names tenant-east. What should /contract/tenant/tenant-west return in the checked fixture?",
     ["200 with the west row", "403 from tenant ownership", "401 from signature validation"], 1,
     "The token is trusted and has the scope, but the managed service rejects a different tenant argument."),
    ("A trusted tenant-east token has receipt.write but calls a receipt.read endpoint. Which layer denies it?",
     ["The endpoint scope rule", "The SQL tenant predicate", "The token signature verifier"], 0,
     "The filter chain requires SCOPE_receipt.read before invoking the service."),
    ("A trusted token has receipt.read but omits tenant_id. What does the local decoder do?",
     ["Uses the URL tenant", "Returns an authentication failure", "Reads every tenant row"], 1,
     "The required tenant claim validator rejects the token before principal conversion."),
    ("Can X-Tenant: tenant-west override a validated tenant-east JWT in the source-kit context?",
     ["Yes, headers have priority", "No, the header is ignored for ownership", "Only when the path matches"], 1,
     "The test sends a spoofed header in both accepted and denied requests; the signed claim remains the identity source."),
    ("R-41 exists for east and west. What must the repository lookup bind?",
     ["Receipt ID only", "Receipt ID and trusted tenant ID", "A caller-supplied display name"], 1,
     "The scoped H2 query uses both values; filtering after an unscoped read is too late."),
    ("What does the local JWT tenant test leave unproved?",
     ["Its own MockMvc status assertions", "Remote issuer rotation and deployed proxy behavior", "That two H2 rows exist"], 1,
     "The test uses temporary keys, a local web context and H2; remote identity and deployment need separate checks."),
]
assert len(quiz["data"]["questions"]) == 12
quiz["data"]["questions"].extend(dict(prompt=prompt, options=options, answer=answer, explanation=explanation)
    for prompt, options, answer, explanation in questions)
quiz["summary"] = "Eighteen explained questions on Spring MVC, JWT and tenant security boundaries."
related = ["spring/jwt-tenant-principal", "spring/scope-versus-tenant-access",
    "spring/tenant-claim-required", "spring/tenant-jdbc-predicate",
    "spring/jwt-web-context-test"]
links = "".join('<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>"
    for path in related)
quiz["body"] = quiz["body"].replace("</ul><h2>Check your reasoning</h2>",
    links + "</ul><h2>Check your reasoning</h2>")
quiz["updated_at"] = datetime.datetime.now(datetime.UTC).isoformat()
FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"quiz": quiz["path"], "questions": len(quiz["data"]["questions"])}))
