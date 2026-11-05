"""Add a scored browser self-check for the Cloud and AI Spring boundary lessons."""

import copy
import datetime
import html
import json
import pathlib
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILE = ROOT / "src/data/fixtures.json"
rows = json.loads(FILE.read_text())
by = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
path = "quizzes/spring-cloud-ai"
assert path not in by

questions = [
    ("A Boot 4 service resolves a Cloud starter but fails when its context starts. What should the team check first?", ["Release-train compatibility and the resolved dependency tree", "The route's CSS", "Only the Java compiler version"], 0, "Dependency resolution alone does not prove Cloud auto-configuration works with the selected Boot line."),
    ("A receipt worker cannot operate correctly without remote lease settings. Which Config Server import matches that rule?", ["A required configserver import", "An optional configserver import with silent defaults", "No import and an unbounded retry loop"], 0, "A required import makes missing remote configuration a startup failure; test that failure explicitly."),
    ("A discovery registry returns an instance for stock-ledger. What has that proved?", ["It supplied a routing candidate", "The caller has receipt.write permission", "The target row belongs to the caller's tenant"], 0, "Routing information is not caller identity or row authorization."),
    ("A POST times out after the server commits seven reserved units. What makes replay safe?", ["A durable tenant-scoped idempotency decision with a request fingerprint", "Selecting a different instance", "Adding one more client retry"], 0, "The caller cannot infer rollback from the missing response; replay needs a persisted decision."),
    ("The stock ledger's circuit is open. Which fallback is safe for a reservation command?", ["An explicit unavailable result without a write", "A successful reservation from cached stock", "An ordinary success response with a hidden warning"], 0, "A cache cannot prove the current write committed."),
    ("A gateway receives X-Tenant: north from a browser. Where should the receipt service get its tenant rule?", ["A verified principal and tenant-scoped data predicate", "The browser header alone", "The public route name"], 0, "The downstream service must enforce ownership with trusted identity, even when the edge also authenticates."),
    ("Retries are enabled in the gateway, client and consumer. What risk needs a shared budget?", ["One request multiplying into many upstream attempts", "Too few DNS names", "A shorter compiled class file"], 0, "Independent retry layers amplify load and tail latency."),
    ("A RAG prompt says to use only north-tenant data, but retrieval searches all tenants. What is missing?", ["An authenticated tenant filter before prompt assembly", "A stronger wording in the prompt", "A larger top-k value"], 0, "The retrieval query must constrain candidates before private text reaches the model."),
    ("A retrieved supplier note tells the assistant to ignore authorization. How should the application treat that text?", ["As untrusted document content", "As a new system instruction", "As proof of tenant membership"], 0, "Document text does not control application policy or tool permissions."),
    ("A model requests reserve(receiptId, tenantId). Which tenant should the tool use?", ["The verified caller's tenant from application context", "The model's tenantId argument", "The first tenant returned by search"], 0, "Tool arguments are model output; authorization uses trusted caller context."),
    ("Two users submit the same conversation ID. What must a memory lookup include?", ["Verified tenant and user ownership", "Only the opaque conversation ID", "Only the model provider name"], 0, "Conversation IDs are selectors, not authorization proof."),
    ("A model returns syntactically valid JSON requesting 47 units against a 12-unit balance. What happens next?", ["Validate business limits and current state before any write", "Commit because the JSON parsed", "Ask the model to claim the reservation succeeded"], 0, "Shape validation cannot establish available stock, version, scope or tenant ownership."),
    ("A model refuses one hostile prompt in a trial run. Which test still proves the security boundary?", ["A deterministic test that denies the unauthorized read or tool call", "Only a higher refusal rate", "A screenshot of the model answer"], 0, "Safety enforcement belongs to code that runs for every data read and side effect."),
    ("A streaming answer's browser disconnects. Which operational check matters?", ["Provider work is cancelled or bounded after disconnect", "The page keeps its spinner forever", "The response is retried without a caller"], 0, "Abandoned generation can keep consuming remote capacity and quota."),
]

review_paths = [
    "spring/cloud-release-train", "spring/cloud-config-import", "spring/cloud-client-retry",
    "spring/cloud-circuit-breaker", "spring/cloud-gateway-tenant", "spring/ai-chat-budget",
    "spring/ai-rag-tenant-filter", "spring/ai-prompt-injection", "spring/ai-tool-authorization",
    "spring/ai-memory-isolation", "spring/ai-structured-output", "spring/ai-evaluation-boundary",
]
assert all(target in by for target in review_paths)
body = "<p>A Spring self-check asks where Cloud routing and model output stop, and where application-owned policy begins.</p>"
body += "<h2>Review before answering</h2><ul>" + "".join(
    '<li><a href="/' + target + '">' + html.escape(by[target]["title"]) + "</a></li>"
    for target in review_paths) + "</ul>"
body += "<h2>Check your reasoning</h2><p>Answer every question and inspect each explanation. This browser self-check is not a credential, a live Cloud integration test or a model evaluation.</p>"
body += "<h3>Common Mistakes</h3><p>A route is not identity, parsed JSON is not authorization, and a model refusal is not a data-access control.</p>"

row = copy.deepcopy(by["quizzes/spring-core"])
row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), path=path,
    title="Spring Cloud and AI boundary quiz", summary="Check Config Server startup, retry safety, tenant retrieval, tool permissions and model-output validation.",
    body=body, sort_order=740, tags=["spring", "spring-boot", "spring-cloud", "spring-ai", "quiz"],
    published_at=stamp, created_at=stamp, updated_at=stamp)
def positioned_question(index, prompt, options, answer, explanation):
    shift = index % len(options)
    shifted = options[shift:] + options[:shift]
    return {"prompt": prompt, "options": shifted,
            "answer": (answer - shift) % len(options), "explanation": explanation}


row["data"] = {"questions": [
    positioned_question(index, prompt, options, answer, explanation)
    for index, (prompt, options, answer, explanation) in enumerate(questions)],
    "duration_minutes": 12, "subject_root": "spring/spring-boot", "section_path": "spring/quizzes",
    "content_format": "html", "seo_ready": True}
rows.append(row)
hub = by["spring/quizzes"]
hub["data"]["modules"].append({"title": "Spring Cloud and AI boundaries", "summary": "Fourteen decisions across startup, calls, retrieval and tools.", "lessons": [path]})
hub["body"] += '<h2>Spring Cloud and AI self-check</h2><p><a href="/' + path + '">' + row["title"] + "</a></p>"
hub["updated_at"] = stamp
FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(questions), "Spring Cloud and AI questions")
