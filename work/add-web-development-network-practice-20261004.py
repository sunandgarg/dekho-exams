"""Add a network cutover project and assessment to the local drafts."""
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


hub_path = "web-tech/network-transport-and-domain-operations"
lessons = [
    "web-tech/dns-ttl-negative-cache-and-cutover-planning",
    "web-tech/tls-certificate-rotation-and-hsts-scope",
    "web-tech/http2-http3-negotiation-and-fallback-testing",
    "web-tech/early-data-replay-and-safe-request-admission",
]
project_path = "web-tech/permit-domain-cutover-and-transport-project"
quiz_path = "quizzes/web-development-network-transport-operations"
assert project_path not in by_path and quiz_path not in by_path

project = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
project.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)),
    path=project_path,
    title="Project: permit domain cutover and transport recovery",
    summary="Move a permit portal to a new origin while preserving DNS, certificate, protocol, and request safety.",
    sort_order=3512,
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
    "Move the permit portal for district 47 from one origin pool to another. Browsers, recursive DNS resolvers, and monitoring probes disagree briefly about which address is current. A stale negative answer may hide a new verification name, and a short record TTL does not erase an older cached answer. Both origin pools must serve a valid certificate and the same session rules while traffic overlaps. The service advertises newer transport where it works, then falls back cleanly through constrained networks. Reviewers submit case mutations during the change; replayed early requests must never create a second approval. Write down the rollback decision before editing DNS."
)
project["body"] += "<h2>Build contract</h2><ul>" + "".join(
    "<li>" + html.escape(item) + "</li>"
    for item in [
        "Inventory authoritative records, resolver observations, negative-answer lifetimes, and the old origin's latest safe retirement time. Probe both endpoints through the overlap window.",
        "Issue and test the replacement certificate before routing users to it. Roll out HSTS scope only after every covered host serves HTTPS and recovery remains possible.",
        "Test HTTP/2 and HTTP/3 through a normal network and a UDP-blocked network. Preserve equivalent authorization, cache rules, and error handling on fallback.",
        "Classify early data at the gateway. Deny or retry unsafe mutations without applying side effects twice; keep an idempotency key and a server-owned operation result for approved writes.",
    ]
) + "</ul>"
project["body"] += "<h2>Implementation checkpoint</h2><pre><code class=\"language-javascript\">" + html.escape(
    'function permitEarlyRequest(method, pathname) {\n'
    '  const publicRead = method === "GET" && pathname === "/permit/help";\n'
    '  return publicRead ? "admit-with-cache-policy" : "wait-for-handshake";\n'
    '}\n'
    'console.log(permitEarlyRequest("POST", "/permit/47/approve"));\n'
    '// Output: wait-for-handshake',
    quote=False,
) + "</code></pre>"
project["body"] += "<h2>Cost and boundaries</h2>" + paragraph(
    "A cutover keeps both origin pools, certificate paths, and rollback capacity alive at once. DNS response time is not the only delay: older positive answers, negative caches, connection reuse, and retrying clients all extend the overlap. The request classifier costs O(1) per admission decision for a fixed route table; the operational cost is proving that every route and downstream side effect obeys the classification. Newer transport adds a second network path to test, not a second authorization model. Track answer age, connection protocol, TLS failures, replay rejections, mutation deduplication, and origin-specific error rates without logging session secrets."
)
project["body"] += "<h2>Failure drill</h2>" + paragraph(
    "First, cache the old answer just before the DNS edit and query a verification name before it exists. Publish the new records, then prove the old origin still handles the stale answer and the new name stays invisible until negative caching expires. Next, remove a certificate from one origin pool in staging: the probe must fail before public routing changes. Block UDP on a client path and confirm it completes a permitted read over the fallback protocol. Finally, replay a case approval as early data and after the handshake. Only one approval may be committed; a rejected early attempt must have a clear retry path that does not assume the first request failed harmlessly."
)
project["body"] += "<h2>Acceptance checks</h2><ul>" + "".join(
    "<li>" + html.escape(item) + "</li>"
    for item in [
        "Both origins pass certificate, host-routing, session, and private-cache checks throughout the DNS overlap.",
        "A stale positive or negative answer changes timing but cannot strand users or hide the rollback route indefinitely.",
        "UDP-blocked clients retain the same permitted behavior through protocol fallback.",
        "Replayed or retried case mutations produce one committed result and a traceable response.",
    ]
) + "</ul>"
project["body"] += "<h3>Common Mistakes</h3><ul><li>Removing the old origin as soon as the record is edited.</li><li>Expanding HSTS coverage before every subdomain is ready.</li><li>Using the request method alone as proof that early data is harmless.</li></ul>"
project["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["data"]["related"]) + ".</p>"
entries.append(project)
by_path[project_path] = project

questions = [
    ("A DNS record was shortened to a low TTL just before cutover. What may still use the old address?", ["Resolvers that cached the prior longer TTL", "Only browsers with JavaScript disabled", "No client after the edit"], 0, "A resolver can keep the answer it received under the previous TTL; lowering the current record does not recall that cached response."),
    ("A previously missing verification name now exists. Why might a resolver still report no answer?", ["The certificate is not renewed", "A negative answer is still cached", "HTTP/3 is blocked"], 1, "Negative answers have their own caching lifetime, so publication can precede visibility through a resolver that cached the absence."),
    ("When can the old origin pool be retired safely?", ["Immediately after an authoritative edit", "After the new pool passes one probe", "After overlap evidence covers stale answers and active connections"], 2, "The retirement decision must account for earlier cached answers, connection reuse, and the ability to serve users arriving at the old address."),
    ("What should happen before traffic reaches a replacement origin?", ["Test its certificate and host routing", "Enable HSTS on every subdomain", "Delete the rollback record"], 0, "A replacement origin needs the right certificate chain and host behavior before DNS or routing sends browsers to it."),
    ("What is the risk of widening HSTS to subdomains too early?", ["It only slows image loading", "An unready subdomain may become unreachable over HTTP", "It disables DNS caching"], 1, "Covered browsers will require HTTPS for those names, so an unready host can become inaccessible until a valid HTTPS path is restored."),
    ("A client cannot use UDP on its current network. What should the transport plan prove?", ["Every write becomes a GET", "The user must install a plugin", "The application still works through a tested fallback"], 2, "A transport upgrade cannot be a required path for users behind a network that blocks it; fallback must preserve the same app behavior."),
    ("Why should authorization be checked on both newer and fallback protocols?", ["The protocols carry requests through different paths", "Fallback traffic is always anonymous", "Certificates replace object permission"], 0, "Different network paths must arrive at the same permission decision; protocol negotiation must not create a weaker route."),
    ("What does a successful HTTP/3 probe alone establish?", ["All networks now support it", "That one path worked; fallback still needs testing", "TLS rotation is complete"], 1, "A successful probe says little about UDP-blocked networks, proxy behavior, or older clients, which need explicit fallback tests."),
    ("Which early request is safest to admit under a narrow, audited policy?", ["A payment capture POST", "An approval mutation with a new id", "A public read with controlled cache behavior"], 2, "Early data can be replayed, so admission should be limited to operations whose semantics and caching make repetition harmless."),
    ("A replayable early request reaches a case approval route. What is the default action?", ["Wait for the full handshake or reject with a retry signal", "Approve twice then repair later", "Trust the browser to prevent replay"], 0, "A case approval has a side effect and cannot rely on the transport to prevent replay before handshake completion."),
    ("A client retries an approval after an early-data rejection. What prevents duplicate commitment?", ["A shorter DNS TTL", "Server-owned idempotency and operation state", "The HTTP version string"], 1, "A stable idempotency key and stored operation result let the server recognize a retry even when the client cannot tell what happened first."),
    ("What should a cutover dashboard separate during the overlap window?", ["Only successful requests", "Only browser brands", "Origin, protocol, TLS, and mutation outcome"], 2, "Separate dimensions reveal whether a failure belongs to the old or new origin, a transport path, certificate handling, or a retried write."),
]
assert len(questions) == 12 and [sum(question[2] == index for question in questions) for index in range(3)] == [4, 4, 4]
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
    path=quiz_path,
    title="Web Development: network transport operations quiz",
    summary="Twelve explained choices about DNS overlap, TLS scope, protocol fallback, and replay-safe requests.",
    sort_order=3513,
    created_at=stamp,
    updated_at=stamp,
    published_at=stamp,
)
quiz["data"] = {
    "subject_root": "web-tech/web-technology",
    "section_path": "web-tech/quizzes",
    "content_format": "html",
    "seo_ready": False,
    "questions": [
        {"prompt": prompt, "options": options, "answer": answer, "explanation": explanation}
        for prompt, options, answer, explanation in questions
    ],
}
quiz["body"] = paragraph(quiz["summary"] + " Choose an answer, inspect its explanation, then return to the related lesson for a missed boundary.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in [hub_path] + lessons + [project_path]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path["web-tech/web-technology/project"]
project_hub["data"]["modules"][0]["lessons"].append(project_path)
project_hub["body"] += "<h2>Network cutover project</h2><p>" + link(project_path) + " — " + html.escape(project["summary"]) + "</p>"
project_hub["updated_at"] = stamp
quiz_hub = by_path["web-tech/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Network transport check</h2><p>" + link(quiz_path) + " — " + html.escape(quiz["summary"]) + "</p>"
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
root_entry["body"] += "<h2>Network transport practice</h2><p>" + link(project_path) + "; " + link(quiz_path) + ".</p>"
root_entry["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": 1, "new_quizzes": 1, "new_questions": len(questions), "answer_positions": {str(index): sum(question[2] == index for question in questions) for index in range(3)}}))
