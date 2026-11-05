"""Add ingress rollout project and assessment drafts."""
import copy
import datetime
import html
import json
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
by_path = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def paragraph(value):
    return "<p>" + html.escape(value) + "</p>"


def link(path):
    assert path in by_path, path
    return '<a href="/' + html.escape(path, quote=True) + '">' + html.escape(by_path[path]["title"]) + "</a>"


hub_path = "web-tech/ingress-proxy-and-upstream-contracts"
lessons = [
    "web-tech/trusted-proxy-hops-and-forwarded-client-identity",
    "web-tech/host-authority-routing-and-default-deny",
    "web-tech/ingress-health-readiness-and-connection-drain",
    "web-tech/proxy-body-budgets-timeouts-and-retry-ownership",
]
project_path = "web-tech/permit-ingress-cutover-and-safe-retry-project"
quiz_path = "quizzes/web-development-ingress-upstream-contracts"
assert project_path not in by_path and quiz_path not in by_path

project = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
project.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)),
    path=project_path,
    title="Project: permit ingress cutover and safe retry",
    summary="Route known hosts through trusted proxies while draining nodes and bounding upload and write retries.",
    sort_order=3635,
    created_at=stamp,
    updated_at=stamp,
    published_at=stamp,
)
project["data"] = {
    "subject_root": "web-tech/web-technology",
    "section_path": "web-tech/web-technology/project",
    "content_format": "html",
    "seo_ready": False,
    "kind": "project",
    "author_path": "authors/aitrove-editorial",
    "reading_minutes": 9,
    "related": [hub_path] + lessons,
}
project["body"] = paragraph(
    "Move a permit portal from one ingress path to another without weakening request trust. The public guide, reviewer app, and case API have distinct hostnames. Two known proxies forward traffic to six API replicas. A reviewer may upload inspection evidence while another approves a case; a rollout drains one replica with long-lived sockets and short requests in flight. The new ingress must reject a direct-origin request with forged client headers, reject unknown hosts, admit only ready upstreams, and keep request-body and retry behavior inside documented budgets. A broken upstream connection after approval does not prove the write failed."
)
project["body"] += "<h2>Build contract</h2><ul>" + "".join(
    "<li>" + html.escape(item) + "</li>"
    for item in [
        "Restrict origin reachability, strip client-supplied forwarding claims at the public edge, and trust only the known proxy hop chain.",
        "Map each allowed host to a certificate, backend, cookie scope, and configured canonical origin; reject unknown and revoked authorities.",
        "Use separate liveness and readiness signals. Stop new admission before a bounded drain and spread long-lived client reconnects.",
        "Apply route-specific body caps and total deadlines; let only classified replay-safe reads retry automatically within a small budget.",
    ]
) + "</ul>"
project["body"] += '<h2>Implementation checkpoint</h2><pre><code class="language-javascript">' + html.escape(
    'function ingressDecision(knownHost, trustedPeer, readyBackend, operationKind) {\n'
    '  if (!knownHost || !trustedPeer) return "reject";\n'
    '  if (!readyBackend) return "unavailable";\n'
    '  return operationKind === "approval" ? "forward-once" : "forward";\n'
    '}\n'
    'console.log(ingressDecision(true, false, true, "approval"));\n'
    '// Output: reject',
    quote=False,
) + "</code></pre>"
project["body"] += "<h2>Cost and boundaries</h2>" + paragraph(
    "Host and trusted-hop checks are small per-request lookups, yet their configuration must be updated for every domain or proxy rollout. Health probes recur across the fleet and need thresholds that avoid flapping. A drain consumes old capacity for its grace period; too little grace interrupts exports and sockets, while too much slows deployment. Body buffering consumes edge memory or disk proportional to concurrent upload bytes. A retry adds upstream work and can duplicate an effect if the origin committed before the connection failed. Record rejected authority, forwarding failures, ready-node count, drain completion, buffered bytes, timeout phase, and stable operation identity without copying private request bodies into logs."
)
project["body"] += "<h2>Failure drill</h2>" + paragraph(
    "Reach the origin directly with a forged office address and prove it cannot be accepted as trusted. Send an old test hostname and a revoked customer hostname through a valid TLS connection; neither may route to the private reviewer app. Start a new node with its port open but its policy table unavailable and verify readiness prevents admission. Drain an old node under 63 short requests and 900 sockets, then measure completion and reconnect surge. Upload 63 megabytes to a 47-megabyte route and confirm early ingress rejection. Finally, commit an approval and drop the upstream connection before its response; any retry must use the same server-owned operation identity and produce one audit event."
)
project["body"] += "<h2>Acceptance checks</h2><ul>" + "".join(
    "<li>" + html.escape(item) + "</li>"
    for item in [
        "A forged address or unknown host cannot change tenant routing, redirect origin, or permission.",
        "Not-ready and draining nodes receive no new ordinary requests.",
        "Body-size and total-time failures end within their route budgets and clean staged data.",
        "A lost approval response does not create a second committed effect.",
    ]
) + "</ul>"
project["body"] += "<h3>Common Mistakes</h3><ul><li>Trusting forwarding headers from a directly reachable origin.</li><li>Making the private app the catch-all host.</li><li>Enabling proxy retries for every failed upstream connection.</li></ul>"
project["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["data"]["related"]) + ".</p>"
entries.append(project)
by_path[project_path] = project

questions = [
    ("A direct origin request carries a forwarded office address. What should the origin trust?", ["Its verified peer policy, not that header", "The first address in the header", "The longest header value"], 0, "A direct caller can forge forwarding text; only an authenticated or network-restricted proxy path may supply trusted metadata."),
    ("Where should client-supplied forwarding fields first be removed or replaced?", ["In an unrelated browser tab", "At the first trusted public boundary", "Only after a failed database query"], 1, "The public ingress must establish a controlled metadata chain before later proxies or the app use those claims."),
    ("Does a trusted client address grant access to permit case 47?", ["Yes, for office networks", "Only while the cache is warm", "No; session and object permission still decide"], 2, "Network address is an abuse or diagnostic signal, not proof of the user's identity or right to a private case."),
    ("An unknown host reaches the ingress. What is the safe default?", ["Reject instead of routing to the private app", "Route to the most privileged service", "Build an account link from it"], 0, "A catch-all private backend can serve content under unintended domains and contaminate generated links."),
    ("Where should a password reset link obtain its base origin?", ["The raw request Host", "Configured canonical origin", "The last proxy error message"], 1, "The application's approved origin is a server-owned value; a request host can be supplied by an attacker or misrouted proxy."),
    ("What if TLS name and HTTP authority disagree?", ["Always accept the HTTP value", "Always accept the TLS value", "Apply the declared pair policy before forwarding"], 2, "The routing layer must decide whether that pair is allowed rather than assuming the two names necessarily match."),
    ("A process port opens before policy data loads. Which probe may pass first?", ["Liveness, while readiness remains false", "Readiness for approvals", "Every request immediately"], 0, "An open process can be alive but still unable to handle its assigned business routes safely."),
    ("What should happen before terminating an old replica during rollout?", ["Add new writes to a cache", "Stop new admission and drain in-flight work", "Delete all session records"], 1, "A drain interval allows bounded completion and a documented reconnect path for long-lived clients."),
    ("What can an over-sensitive shared-dependency readiness probe cause?", ["A smaller HTML file", "Fewer user sessions only", "Every instance dropping out of rotation together"], 2, "If one shared pause marks every instance unready, the load balancer may have no usable destination during recovery."),
    ("An upload exceeds the route cap. Where should coarse rejection occur?", ["At ingress before full buffering", "Only after the app stores it", "After the export job runs"], 0, "Early ingress limits avoid consuming the full buffer and origin resources for a request that cannot be accepted."),
    ("Why is a per-read timeout insufficient for a slow trickle upload?", ["It always includes full request duration", "Each small read may reset the interval", "It prevents all bytes from arriving"], 1, "A sender can keep making progress just before an inactivity timer expires; a total deadline is a separate bound."),
    ("An approval commits and then its upstream connection fails. Can the proxy infer no effect occurred?", ["Yes, because there was no response", "Yes, if another node is healthy", "No; retry needs operation identity and deduplication"], 2, "The origin may have committed before the connection broke, so blindly replaying the mutation can duplicate side effects."),
]
assert len(questions) == 12 and [sum(question[2] == index for question in questions) for index in range(3)] == [4, 4, 4]
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: ingress and upstream contracts quiz",
            summary="Twelve explained choices about proxy trust, host routing, readiness, body budgets, and retries.",
            sort_order=3636, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes", "content_format": "html", "seo_ready": False,
                "questions": [{"prompt": prompt, "options": options, "answer": answer, "explanation": explanation}
                              for prompt, options, answer, explanation in questions]}
quiz["body"] = paragraph(quiz["summary"] + " Choose an answer, inspect its explanation, then return to the related lesson for a missed boundary.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in [hub_path] + lessons + [project_path]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path["web-tech/web-technology/project"]
project_hub["data"]["modules"][0]["lessons"].append(project_path)
project_hub["body"] += "<h2>Ingress rollout project</h2><p>" + link(project_path) + " — " + html.escape(project["summary"]) + "</p>"
project_hub["updated_at"] = stamp
quiz_hub = by_path["web-tech/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Ingress contracts check</h2><p>" + link(quiz_path) + " — " + html.escape(quiz["summary"]) + "</p>"
quiz_hub["updated_at"] = stamp
hub = by_path[hub_path]
hub["body"] += "<h2>Practice and check</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + ".</p>"
hub["updated_at"] = stamp
for path in lessons:
    entry = by_path[path]
    entry["body"] += "<h2>Apply and check</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + ".</p>"
    entry["data"]["related"].extend([project_path, quiz_path])
    entry["updated_at"] = stamp
root_entry = by_path["web-tech/web-technology"]
root_entry["body"] += "<h2>Ingress rollout practice</h2><p>" + link(project_path) + "; " + link(quiz_path) + ".</p>"
root_entry["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": 1, "new_quizzes": 1, "new_questions": len(questions), "answer_positions": {str(index): sum(question[2] == index for question in questions) for index in range(3)}}))
