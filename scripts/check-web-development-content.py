"""Check local Web Development lessons, routes, links, and runnable examples."""

import ast
import html
import json
import re
import subprocess
import tempfile
from html.parser import HTMLParser
from pathlib import Path

root = Path(__file__).resolve().parents[1]
entries = json.loads((root / "src/data/fixtures.json").read_text())
by_path = {entry["path"]: entry for entry in entries}
assert len(by_path) == len(entries), "Duplicate fixture path"
web_entries = [entry for entry in entries if entry["path"].startswith("web-tech/")]
quiz_entries = [entry for entry in entries if entry["path"].startswith("quizzes/web-development-")]
assert len(web_entries) == 515, len(web_entries)
assert len(quiz_entries) == 56, len(quiz_entries)

allowed = {"p", "h2", "h3", "ul", "li", "strong", "pre", "code", "a"}
banned = re.compile(r"\b(?:delve|leverage|harness|foster|streamline|showcase|navigate|demystify|furthermore|moreover|additionally|robust|crucial|pivotal|multifaceted|bespoke|seamless|dynamic|quintessential|nuanced|powerful|versatile)\b", re.I)


class BodyParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.links = []
        self.code_classes = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        attr_map = dict(attrs)
        if tag == "a":
            self.links.append(attr_map.get("href", ""))
        if tag == "code":
            self.code_classes.append(attr_map.get("class", ""))


for entry in web_entries + quiz_entries:
    body = entry.get("body", "")
    assert body.startswith("<p>"), entry["path"]
    prose_only = re.sub(r"<pre>.*?</pre>", "", body, flags=re.S)
    assert not re.search(r"https?://", prose_only), entry["path"]
    assert not re.search(r"\b(?:sample content|local preview|lorem ipsum|TODO|TBD)\b", body, re.I), entry["path"]
    assert not banned.search(re.sub(r"<pre>.*?</pre>", "", body, flags=re.S)), entry["path"]
    assert entry["data"]["content_format"] == "html", entry["path"]
    parser = BodyParser()
    parser.feed(body)
    assert set(parser.tags) <= allowed, (entry["path"], set(parser.tags) - allowed)
    for target in parser.links:
        assert target.startswith("/") and target[1:] in by_path, (entry["path"], target)
        assert by_path[target[1:]]["status"] == "published", (entry["path"], target)
    for code_class in parser.code_classes:
        assert code_class.startswith("language-"), (entry["path"], code_class)
    for module in entry["data"].get("modules", []):
        for target in module["lessons"]:
            assert target in by_path, (entry["path"], target)
            assert by_path[target]["status"] == "published", (entry["path"], target)

reachable = {"web-tech/web-technology"}
frontier = ["web-tech/web-technology"]
while frontier:
    current = frontier.pop()
    for module in by_path[current]["data"].get("modules", []):
        for target in module["lessons"]:
            if target not in reachable:
                reachable.add(target)
                frontier.append(target)
assert {entry["path"] for entry in web_entries + quiz_entries} <= reachable, "Unreachable Web Development route"

broad_hubs = [
    "web-tech/frontend-application-architecture", "web-tech/backend-api-systems",
    "web-tech/data-persistence", "web-tech/media-and-live-updates",
    "web-tech/offline-and-device-capabilities", "web-tech/deployment-and-scale",
    "web-tech/content-discovery-and-structure",
    "web-tech/identity-and-application-security", "web-tech/integration-and-verification",
    "web-tech/inclusive-interface-engineering", "web-tech/internationalization-and-content-delivery",
    "web-tech/typed-frontend-and-component-platform", "web-tech/browser-security-and-data-stewardship",
    "web-tech/application-search-and-retrieval", "web-tech/quality-and-capacity-engineering",
    "web-tech/css-layout-and-interface-systems", "web-tech/browser-execution-and-resource-lifecycle",
    "web-tech/api-mutation-and-failure-contracts",
    "web-tech/server-rendering-and-client-data-flow", "web-tech/forms-and-data-entry-workflows",
    "web-tech/navigation-history-and-page-lifecycle", "web-tech/http-delivery-and-cache-ownership",
    "web-tech/streaming-and-large-data-interfaces", "web-tech/complex-accessible-interactions",
    "web-tech/production-signals-and-incident-decisions", "web-tech/cross-tab-and-offline-data-coordination",
    "web-tech/authorization-and-tenant-boundaries", "web-tech/data-retention-export-and-erasure",
    "web-tech/browser-capabilities-and-permission-lifecycle", "web-tech/overlays-scroll-and-mobile-viewport",
    "web-tech/accessible-content-and-media", "web-tech/privacy-aware-external-integrations",
    "web-tech/web-push-and-notification-delivery",
    "web-tech/passkeys-and-account-assurance", "web-tech/checkout-and-payment-state",
    "web-tech/file-ingestion-and-private-asset-lifecycle", "web-tech/outbound-email-and-delivery-state",
    "web-tech/feature-release-and-experiment-controls", "web-tech/graphql-query-and-resolver-boundaries",
    "web-tech/webassembly-and-browser-compute", "web-tech/webrtc-and-peer-media-sessions",
    "web-tech/motion-and-view-change-contracts", "web-tech/multi-region-web-state-and-recovery",
    "web-tech/interactive-graphics-and-canvas-boundaries", "web-tech/rich-document-editing-and-safe-content",
    "web-tech/embedded-interfaces-and-cross-window-contracts", "web-tech/frontend-build-and-artifact-integrity",
    "web-tech/offline-storage-and-upgrade-safety", "web-tech/browser-cryptography-and-key-custody",
    "web-tech/web-component-contracts-and-interoperability", "web-tech/progressive-browser-compatibility",
    "web-tech/background-workflow-reliability", "web-tech/abuse-resistant-public-endpoints",
    "web-tech/model-backed-web-application-boundaries",
    "web-tech/on-demand-media-playback-and-delivery",
    "web-tech/browser-extension-trust-and-lifecycle",
    "web-tech/geospatial-web-interfaces-and-spatial-queries",
    "web-tech/federated-identity-and-session-lifecycle",
    "web-tech/api-contract-evolution-and-client-migration",
    "web-tech/edge-runtime-and-origin-boundaries",
    "web-tech/realtime-connection-and-event-delivery",
    "web-tech/network-transport-and-domain-operations",
    "web-tech/database-capacity-and-online-change-operations",
    "web-tech/application-cache-consistency-and-capacity",
    "web-tech/ingress-proxy-and-upstream-contracts",
    "web-tech/browser-performance-diagnosis-and-measurement",
    "web-tech/react-state-and-rendering-boundaries",
    "web-tech/vue-reactivity-and-component-boundaries",
    "web-tech/angular-signals-and-delivery-boundaries",
    "web-tech/svelte-reactivity-and-server-boundaries",
    "web-tech/nextjs-app-router-delivery-boundaries",
    "web-tech/express-request-and-process-boundaries",
    "web-tech/django-request-and-persistence-boundaries",
    "web-tech/fastapi-contract-and-resource-boundaries",
    "web-tech/laravel-policy-query-and-queue-boundaries",
    "web-tech/flask-context-and-service-boundaries",
    "web-tech/rails-request-record-and-job-boundaries",
    "web-tech/cms-content-publication-and-preview-boundaries",
    "web-tech/spring-boot-web-service-boundaries",
    "web-tech/node-native-http-and-runtime-boundaries",
    "web-tech/php-request-session-and-persistence-boundaries",
]
for path in broad_hubs:
    modules = by_path[path]["data"]["modules"]
    assert len(modules) == 1 and len(modules[0]["lessons"]) == 4, path
    assert all(by_path[target]["data"]["section_path"] == path for target in modules[0]["lessons"]), path

articles = [entry for entry in web_entries if entry["type"] == "article"]
assert len(articles) == 427, len(articles)
for entry in articles:
    prose = re.sub(r"<pre>.*?</pre>", " ", entry["body"], flags=re.S)
    prose = html.unescape(re.sub(r"<[^>]+>", " ", prose))
    assert len(re.findall(r"\b[\w'-]+\b", prose)) >= 150, (entry["path"], len(prose.split()))
    assert "<h3>Common Mistakes</h3>" in entry["body"], entry["path"]
    assert entry["body"].count('href="/') >= 3, entry["path"]

technical = [entry for entry in articles if entry["data"].get("kind") == "tutorial"]
assert len(technical) == 344, len(technical)
for entry in technical:
    assert '<pre><code class="language-' in entry["body"], entry["path"]
    assert "<h2>Cost and tradeoffs</h2>" in entry["body"] or "<h2>Cost and boundaries</h2>" in entry["body"], entry["path"]

deepened = [entry for entry in technical if entry["data"].get("section_path") in broad_hubs]
assert len(deepened) == 324, len(deepened)
foundation_sections = {
    "web-tech/request-and-browser-foundations", "web-tech/browser-interactions",
    "web-tech/state-and-trust", "web-tech/quality-and-release",
}
foundation = [entry for entry in technical if entry["data"].get("section_path") in foundation_sections]
assert len(foundation) == 20, len(foundation)
assert len(deepened) + len(foundation) == len(technical)
for entry in deepened + foundation:
    prose = re.sub(r"<pre>.*?</pre>", " ", entry["body"], flags=re.S)
    prose = html.unescape(re.sub(r"<[^>]+>", " ", prose))
    assert len(re.findall(r"\b[\w'-]+\b", prose)) >= 480, entry["path"]
    assert "<h2>Failure trace</h2>" in entry["body"], entry["path"]
    assert "<h2>Verification</h2>" in entry["body"], entry["path"]
    assert "<h2>Decision note</h2>" in entry["body"], entry["path"]

projects = [entry for entry in articles if entry["data"].get("kind") == "project"]
assert len(projects) == 81, len(projects)
for entry in projects:
    assert "<h3>Common Mistakes</h3>" in entry["body"], entry["path"]
    assert entry["body"].count('href="/') >= 3, entry["path"]

for path in ("web-tech/getting-started", "web-tech/core-concepts"):
    assert "<h2>Verification</h2>" in by_path[path]["body"], path
    prose = re.sub(r"<pre>.*?</pre>", " ", by_path[path]["body"], flags=re.S)
    prose = html.unescape(re.sub(r"<[^>]+>", " ", prose))
    assert len(re.findall(r"\b[\w'-]+\b", prose)) >= 380, path
for path in ("web-tech/practice-project", "web-tech/case-intake-end-to-end-project", "web-tech/web-release-readiness-project"):
    prose = re.sub(r"<pre>.*?</pre>", " ", by_path[path]["body"], flags=re.S)
    prose = html.unescape(re.sub(r"<[^>]+>", " ", prose))
    assert len(re.findall(r"\b[\w'-]+\b", prose)) >= 400, path

ran = 0
for entry in technical:
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre><h3>Observed output</h3><pre><code class="language-text">(.*?)</code></pre>', entry["body"], re.S)
    if not match:
        continue
    code = html.unescape(match.group(1))
    expected = html.unescape(match.group(2)).strip()
    result = subprocess.run(["node", "-e", code], check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (entry["path"], expected, result.stdout)
    ran += 1
assert ran == 17, ran

search_quality_cases = {
    "web-tech/search-index-freshness-and-rebuilds": "false\ntrue",
    "web-tech/search-query-normalization-and-ranking": "lift 47",
    "web-tech/search-filters-and-result-cursors": "false",
    "web-tech/search-permissions-and-private-results": "[ { caseId: 62, title: 'Lift' } ]",
    "web-tech/test-boundaries-and-evidence-selection": "true",
    "web-tech/deterministic-test-doubles-and-fault-injection": "62",
    "web-tech/accessibility-and-visual-regression-checks": "inspection-note",
    "web-tech/load-tests-and-capacity-budgets": "true",
}
for path, expected in search_quality_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, result.stdout)

layout_css_paths = [
    "web-tech/grid-flex-and-intrinsic-size-contracts",
    "web-tech/container-queries-for-reusable-panels",
    "web-tech/cascade-layers-and-design-token-ownership",
    "web-tech/font-loading-and-motion-fallbacks",
]
for path in layout_css_paths:
    match = re.search(r'<pre><code class="language-css">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    subprocess.run([str(root / "node_modules/.bin/prettier"), "--parser", "css"],
                   input=html.unescape(match.group(1)), check=True, capture_output=True, text=True)

runtime_cases = {
    "web-tech/event-loop-tasks-microtasks-and-paint": ("", "current task / microtask / next task"),
    "web-tech/cooperative-main-thread-scheduling": (
        '\nconst seen = [];\nconst completed = await summarizeInChunks([47, 62, 93], () => seen.length < 2, record => seen.push(record));\nconsole.log(completed, seen.join(","));',
        "false 47,62",
    ),
}
for path, (exercise, expected) in runtime_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1)) + exercise],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, result.stdout)

api_mutation_cases = {
    "web-tech/conditional-writes-and-lost-update-prevention": "412",
    "web-tech/request-deadlines-retries-and-backoff": "true",
    "web-tech/accepted-operations-and-status-resources": "queued",
    "web-tech/structured-api-errors-and-recovery": "case_version_conflict",
}
for path, expected in api_mutation_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, result.stdout)

rendering_form_cases = {
    "web-tech/hydration-and-deterministic-first-render": "true",
    "web-tech/server-data-bootstrap-and-freshness": "false",
    "web-tech/client-cache-keys-and-invalidation": '["case",29,47]',
    "web-tech/optimistic-mutations-and-rollback": "Resolved 6",
    "web-tech/asynchronous-field-validation-races": "false",
    "web-tech/autosave-draft-recovery-and-conflicts": "needs-review",
    "web-tech/case-queue-rendering-and-mutation-project": "false",
    "web-tech/recoverable-case-intake-form-project": "false",
}
for path, expected in rendering_form_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, result.stdout)

for path in ("web-tech/native-form-submission-and-progressive-enhancement",
             "web-tech/multipart-upload-progress-and-retry-boundaries"):
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    subprocess.run(["node", "--check", "--input-type=module"], input=html.unescape(match.group(1)),
                   check=True, capture_output=True, text=True)

navigation_delivery_cases = {
    "web-tech/url-state-and-history-entry-contracts": "push",
    "web-tech/back-forward-cache-and-restored-state": "true",
    "web-tech/route-scroll-and-focus-restoration": "62",
    "web-tech/navigation-prefetch-and-private-data-budget": "false",
    "web-tech/shared-cache-keys-and-private-response-boundaries": "private, no-store",
    "web-tech/stale-revalidation-and-versioned-purges": "false",
    "web-tech/content-negotiation-and-compression-contracts": "hi:br",
    "web-tech/critical-resource-discovery-and-priority": '{"loading":"lazy","priority":"auto"}',
    "web-tech/history-safe-review-journey-project": "true",
    "web-tech/edge-cache-and-critical-resource-project": "false",
}
for path, expected in navigation_delivery_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, result.stdout)

streams_interactions_cases = {
    "web-tech/incremental-response-framing-and-utf8": "2 0",
    "web-tech/stream-backpressure-and-bounded-work": "false",
    "web-tech/stream-cancellation-and-partial-result-contract": "partial",
    "web-tech/large-export-download-and-integrity": "false",
    "web-tech/data-table-versus-interactive-grid": "false",
    "web-tech/combobox-suggestions-and-active-option": "2",
    "web-tech/reorder-controls-without-dragging": "62,47,93",
    "web-tech/async-status-announcements-and-focus": "Case 47 changed elsewhere",
    "web-tech/streamed-case-activity-and-export-project": "false",
    "web-tech/accessible-operations-workspace-project": '{"position":2,"total":3}',
}
for path, expected in streams_interactions_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

operations_sync_cases = {
    "web-tech/trace-context-across-request-and-job": "f" * 32,
    "web-tech/user-journey-slos-and-burn-alerts": '{"allowance":47,"spent":47,"over":false}',
    "web-tech/telemetry-shapes-redaction-and-cardinality": '{"operationId":"op-47","route":"/cases/:id","release":"r29","outcome":"failed"}',
    "web-tech/incident-containment-and-evidence-timeline": "isolate-worker",
    "web-tech/cross-tab-invalidation-and-version-checks": "true",
    "web-tech/offline-outbox-idempotency-and-replay": "conflicted",
    "web-tech/snapshot-delta-cursor-and-gap-recovery": "30",
    "web-tech/collaborative-conflicts-and-presence-expiry": "status",
    "web-tech/case-save-incident-evidence-project": "pending",
    "web-tech/multi-tab-offline-case-review-project": "conflicted",
}
for path, expected in operations_sync_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

authorization_lifecycle_cases = {
    "web-tech/object-level-authorization-for-reads-and-writes": "false",
    "web-tech/tenant-scope-in-cache-and-background-work": "tenant:6:case:47:policy:3",
    "web-tech/permission-revocation-and-active-sessions": "false",
    "web-tech/private-export-authorization-and-artifact-scope": "false",
    "web-tech/retention-inventory-and-expiry-workflows": "true",
    "web-tech/export-and-erasure-job-state": "partial-failure",
    "web-tech/backup-restore-with-deletion-tombstones": "false",
    "web-tech/browser-storage-cleanup-on-account-change": "true",
    "web-tech/tenant-safe-case-export-project": "null",
    "web-tech/verified-data-expiry-project": "false",
}
for path, expected in authorization_lifecycle_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

browser_capability_cases = {
    "web-tech/permission-request-timing-and-manual-fallback": "manual-entry",
    "web-tech/camera-microphone-capture-and-track-cleanup": "true",
    "web-tech/geolocation-accuracy-cancellation-and-retention": "confirm-area",
    "web-tech/clipboard-and-share-activation-fallbacks": "select-and-copy",
    "web-tech/stacking-context-top-layer-and-overlay-contract": "modal-dialog",
    "web-tech/scroll-containers-anchoring-and-chaining": "false",
    "web-tech/pointer-gesture-touch-action-and-alternate-control": "47,89,62",
    "web-tech/visual-viewport-keyboard-and-focused-input": "384",
    "web-tech/field-intake-capability-fallback-project": '{"media":"file-picker","place":"review-estimate"}',
    "web-tech/mobile-review-overlay-and-scroll-project": "47,62,89",
}
for path, expected in browser_capability_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

accessible_privacy_cases = {
    "web-tech/image-alternatives-by-purpose": "View larger evidence photo",
    "web-tech/chart-and-diagram-text-equivalents": '{"direction":"up","amount":24}',
    "web-tech/captions-transcripts-and-media-controls": "false",
    "web-tech/landmarks-headings-and-skip-paths": "route-error-heading",
    "web-tech/third-party-request-and-script-inventory": "widget.partner",
    "web-tech/optional-analytics-event-boundaries": '{"event":"export_action","routeClass":"case-review","outcome":"started"}',
    "web-tech/embedded-widget-storage-and-fallback": "top-level-support",
    "web-tech/preference-change-propagation-and-audit": "false",
    "web-tech/accessible-inspection-report-project": "false",
    "web-tech/privacy-safe-support-and-measurement-project": "false",
}
for path, expected in accessible_privacy_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

push_notification_cases = {
    "web-tech/notification-opt-in-and-channel-preference": "false",
    "web-tech/push-subscription-account-binding-and-rotation": "false",
    "web-tech/private-notification-payload-and-click-routing": '{"kind":"urgent_assignment","title":"New urgent assignment","route":"/assignments"}',
    "web-tech/push-delivery-retries-expiry-and-inbox-fallback": "superseded",
    "web-tech/private-urgent-assignment-alert-project": "false",
}
for path, expected in push_notification_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

passkey_checkout_cases = {
    "web-tech/passkey-registration-challenge-and-credential-binding": "false",
    "web-tech/passkey-assertion-origin-and-signature-verification": "false",
    "web-tech/passkey-conditional-sign-in-and-fallback": '{"passkey":false,"fallback":true}',
    "web-tech/passkey-management-recovery-and-step-up": "false",
    "web-tech/server-priced-order-snapshot-and-money-units": "17200",
    "web-tech/hosted-checkout-session-and-browser-return": "Payment being confirmed",
    "web-tech/payment-webhook-reconciliation-and-idempotent-fulfillment": "fulfill:47:pay-62",
    "web-tech/refunds-reversals-and-payment-ledger-state": "12500",
    "web-tech/passkey-account-lifecycle-project": "false",
    "web-tech/checkout-reconciliation-project": "12500",
}
for path, expected in passkey_checkout_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

file_email_cases = {
    "web-tech/upload-intake-budgets-and-storage-ownership": "false",
    "web-tech/resumable-transfer-parts-and-integrity": "8",
    "web-tech/file-quarantine-inspection-and-derived-previews": "false",
    "web-tech/private-asset-download-revocation-and-expiry": "false",
    "web-tech/email-intent-outbox-and-idempotent-send": "case:47:assignment:6",
    "web-tech/email-template-data-and-account-link-boundaries": "false",
    "web-tech/email-provider-events-bounces-and-suppression": "false",
    "web-tech/sender-identity-reputation-and-message-observability": "0.043",
    "web-tech/private-evidence-file-lifecycle-project": "false",
    "web-tech/account-email-delivery-project": "assignment:47:6",
}
for path, expected in file_email_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

release_graphql_cases = {
    "web-tech/feature-flag-evaluation-scope-and-safe-default": "old",
    "web-tech/gradual-rollout-kill-switch-and-state-compatibility": "true",
    "web-tech/experiment-assignment-exposure-and-metric-integrity": "false",
    "web-tech/flag-telemetry-audit-and-retirement": "true",
    "web-tech/graphql-schema-nullability-and-evolution": "null",
    "web-tech/graphql-resolver-batching-and-tenant-scope": "62,47",
    "web-tech/graphql-operation-cost-and-admission": "null",
    "web-tech/graphql-mutation-errors-and-pagination-contracts": "conflict",
    "web-tech/assignment-panel-release-experiment-project": "stop",
    "web-tech/tenant-safe-graphql-case-api-project": "false",
}
for path, expected in release_graphql_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

browser_compute_peer_cases = {
    "web-tech/wasm-loading-artifact-and-fallback-contract": "javascript",
    "web-tech/wasm-linear-memory-ownership-and-copy-cost": "false",
    "web-tech/wasm-worker-jobs-cancellation-and-result-order": "false",
    "web-tech/wasm-capabilities-isolation-and-performance-budget": "single-worker",
    "web-tech/media-capture-consent-and-track-lifecycle": "false",
    "web-tech/webrtc-signaling-room-auth-and-offer-order": "false",
    "web-tech/webrtc-ice-turn-fallback-and-session-recovery": "notes",
    "web-tech/data-channel-backpressure-and-peer-state": "false",
    "web-tech/local-scan-analysis-worker-project": "false",
    "web-tech/private-peer-consultation-project": "false",
}
for path, expected in browser_compute_peer_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

motion_region_cases = {
    "web-tech/css-motion-state-and-interruption": "closed",
    "web-tech/web-animations-lifecycle-and-cancellation": "false",
    "web-tech/view-transition-navigation-focus-and-fallback": "false",
    "web-tech/reduced-motion-and-rendering-budget": "instant-with-status",
    "web-tech/regional-routing-static-and-private-cache-boundaries": "false",
    "web-tech/replica-lag-read-your-write-and-version-cursors": "false",
    "web-tech/regional-failover-fencing-and-replay": "false",
    "web-tech/regional-data-location-and-operational-evidence": "false",
    "web-tech/case-board-motion-and-route-project": "false",
    "web-tech/two-region-case-service-recovery-project": "false",
}
for path, expected in motion_region_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

graphics_editing_cases = {
    "web-tech/svg-canvas-scene-model-and-hit-testing": "29",
    "web-tech/canvas-pixel-ratio-and-pointer-coordinates": "310",
    "web-tech/canvas-origin-clean-export-and-private-assets": "server",
    "web-tech/accessible-graphic-controls-and-text-equivalents": "Region 29: high severity, seal split",
    "web-tech/editable-input-composition-and-document-model": "false",
    "web-tech/selection-bookmarks-and-transaction-mapping": "52",
    "web-tech/paste-import-sanitization-and-link-policy": "false",
    "web-tech/undo-history-autosave-and-revision-conflicts": "false",
    "web-tech/accessible-inspection-map-export-project": "29",
    "web-tech/versioned-case-note-editor-project": "false",
}
for path, expected in graphics_editing_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

embeds_build_cases = {
    "web-tech/frame-sandbox-capabilities-and-fallback": "allow-scripts,allow-same-origin",
    "web-tech/postmessage-origin-source-schema-and-replay": "true",
    "web-tech/messagechannel-lifetime-and-request-correlation": "2",
    "web-tech/popup-handoff-return-and-window-ownership": "false",
    "web-tech/locked-dependency-resolution-and-clean-installs": "false",
    "web-tech/dependency-admission-scripts-and-provenance": "true",
    "web-tech/external-asset-integrity-and-module-resolution": "true",
    "web-tech/artifact-manifest-rollout-and-rollback-coherence": "false",
    "web-tech/embedded-attachment-viewer-contract-project": "false",
    "web-tech/frontend-artifact-promotion-project": "false",
}
for path, expected in embeds_build_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

offline_crypto_cases = {
    "web-tech/service-worker-activation-and-unsent-work": "false",
    "web-tech/indexeddb-versionchange-and-blocked-tabs": "false",
    "web-tech/browser-storage-quota-eviction-and-recovery": "offer-smaller-file-or-export",
    "web-tech/private-offline-cache-and-account-switch": "false",
    "web-tech/browser-encryption-threat-model-and-key-custody": "false",
    "web-tech/authenticated-encryption-nonce-and-record-binding": "true",
    "web-tech/password-unlock-derivation-and-recovery": "true",
    "web-tech/key-rotation-envelopes-and-device-loss": "false",
    "web-tech/offline-case-review-upgrade-project": "false",
    "web-tech/encrypted-local-draft-lifecycle-project": "false",
}
for path, expected in offline_crypto_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

components_compatibility_cases = {
    "web-tech/custom-element-upgrade-and-reconnection": "false",
    "web-tech/shadow-slots-events-and-focus-contract": "true",
    "web-tech/form-associated-custom-control-and-native-fallback": "null",
    "web-tech/shadow-style-tokens-parts-and-shared-sheets": "#365a7a",
    "web-tech/feature-probes-and-functional-fallbacks": "server-download",
    "web-tech/polyfill-cost-and-target-browser-policy": "false",
    "web-tech/cross-browser-input-and-device-contracts": "true",
    "web-tech/capability-rollout-and-fallback-retirement": "server-preview",
    "web-tech/case-decision-web-component-project": "false",
    "web-tech/progressive-case-export-release-project": "server-download",
}
for path, expected in components_compatibility_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

jobs_abuse_cases = {
    "web-tech/job-admission-idempotency-and-status-resource": "false",
    "web-tech/worker-leases-retries-and-duplicate-effects": "false",
    "web-tech/poison-job-quarantine-and-replay-control": "quarantine",
    "web-tech/scheduled-job-overlap-cancel-and-compensation": "false",
    "web-tech/account-recovery-enumeration-and-throttle-policy": "true",
    "web-tech/expensive-request-work-budgets-and-shed-load": "19",
    "web-tech/human-challenges-accessible-alternatives-and-signal-retention": "false",
    "web-tech/abuse-decision-telemetry-and-false-positive-rollback": "true",
    "web-tech/permit-report-job-recovery-project": "false",
    "web-tech/public-permit-abuse-control-project": "defer",
}
for path, expected in jobs_abuse_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

model_app_cases = {
    "web-tech/model-gateway-identity-and-request-budgets": "defer",
    "web-tech/generated-response-streaming-and-cancel-state": "false",
    "web-tech/retrieved-content-instructions-and-tool-permission": "false",
    "web-tech/model-output-evaluation-and-release-control": "block",
    "web-tech/permission-bound-maintenance-summary-project": "false",
}
for path, expected in model_app_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

media_playback_cases = {
    "web-tech/media-player-source-and-load-state": "Playback unavailable; open the transcript",
    "web-tech/media-byte-ranges-seeking-and-version-identity": "63",
    "web-tech/adaptive-media-buffer-and-fallback-policy": "360p",
    "web-tech/private-media-session-cache-and-timed-text": "false",
    "web-tech/private-inspection-clip-playback-project": "false",
}
for path, expected in media_playback_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

extension_geo_cases = {
    "web-tech/extension-host-permissions-and-user-invocation": "false",
    "web-tech/content-script-isolation-and-dom-mutation": "false",
    "web-tech/extension-background-events-and-durable-state": "false",
    "web-tech/extension-message-contracts-and-page-data-boundary": "false",
    "web-tech/permit-checklist-browser-helper-project": "false",
    "web-tech/coordinate-validation-projection-and-antimeridian": "false",
    "web-tech/map-viewport-tiles-and-request-lifecycle": "false",
    "web-tech/nearby-spatial-search-and-tenant-filter": "false",
    "web-tech/location-consent-precision-and-map-alternatives": "false",
    "web-tech/authorized-facility-map-and-nearby-search-project": "false",
}
for path, expected in extension_geo_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

federation_cases = {
    "web-tech/authorization-code-pkce-and-callback-binding": "false",
    "web-tech/id-token-verification-and-stable-account-identity": "false",
    "web-tech/refresh-token-rotation-and-app-session-boundary": "false",
    "web-tech/federated-account-linking-logout-and-revocation": "false",
    "web-tech/federated-permit-reviewer-sign-in-project": "false",
}
for path, expected in federation_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

api_evolution_cases = {
    "web-tech/response-shape-evolution-and-unknown-values": "read-only-unknown",
    "web-tech/api-version-selection-and-representation-scope": '{"durationHours":3}',
    "web-tech/deprecation-sunset-and-consumer-evidence": "false",
    "web-tech/consumer-contract-matrix-and-expand-contract-release": "false",
    "web-tech/permit-api-client-migration-project": '{"durationMinutes":180}',
}
for path, expected in api_evolution_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

edge_origin_cases = {
    "web-tech/edge-request-normalization-and-origin-trust": "false",
    "web-tech/edge-compute-budgets-and-upstream-fanout": "false",
    "web-tech/edge-cache-locality-invalidation-and-private-scope": "false",
    "web-tech/edge-origin-write-routing-and-consistency": "false",
    "web-tech/edge-permit-case-delivery-project": "false",
}
for path, expected in edge_origin_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

realtime_cases = {
    "web-tech/websocket-handshake-session-and-channel-authorization": "false",
    "web-tech/event-sequence-replay-and-gap-reconciliation": "reconcile-gap",
    "web-tech/socket-fanout-backpressure-and-slow-consumers": "true",
    "web-tech/presence-expiry-heartbeats-and-connection-drain": "unknown",
    "web-tech/live-permit-case-board-project": "load-snapshot",
}
for path, expected in realtime_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

network_cases = {
    "web-tech/dns-ttl-negative-cache-and-cutover-planning": "true",
    "web-tech/tls-certificate-rotation-and-hsts-scope": "true",
    "web-tech/http2-http3-negotiation-and-fallback-testing": "true",
    "web-tech/early-data-replay-and-safe-request-admission": "false",
    "web-tech/permit-domain-cutover-and-transport-project": "wait-for-handshake",
}
for path, expected in network_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

database_operations_cases = {
    "web-tech/connection-pool-budgets-and-queue-admission": "false",
    "web-tech/transaction-retry-deadlock-and-side-effect-boundaries": "restart-transaction",
    "web-tech/resumable-data-backfills-and-reconciliation": "47,62",
    "web-tech/online-index-builds-and-query-plan-release-gates": "false",
    "web-tech/permit-data-change-with-live-traffic-project": "false",
}
for path, expected in database_operations_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

application_cache_cases = {
    "web-tech/cache-aside-fill-races-and-version-guards": "false",
    "web-tech/cache-stampede-singleflight-and-hot-key-budgets": "6",
    "web-tech/cache-memory-eviction-and-degraded-read-paths": "false",
    "web-tech/negative-cache-entries-and-stale-read-contracts": "refresh-or-fail",
    "web-tech/permit-cache-recovery-and-consistency-project": "reject-old-fill",
}
for path, expected in application_cache_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

ingress_cases = {
    "web-tech/trusted-proxy-hops-and-forwarded-client-identity": "null",
    "web-tech/host-authority-routing-and-default-deny": "reject",
    "web-tech/ingress-health-readiness-and-connection-drain": "false",
    "web-tech/proxy-body-budgets-timeouts-and-retry-ownership": "false",
    "web-tech/permit-ingress-cutover-and-safe-retry-project": "reject",
}
for path, expected in ingress_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

browser_diagnosis_cases = {
    "web-tech/field-performance-observation-and-sample-contracts": "paint,navigation",
    "web-tech/interaction-latency-traces-and-main-thread-contention": '{"totalMs":310,"withinBudget":false}',
    "web-tech/retained-dom-memory-and-lifecycle-investigation": "observer-disconnected",
    "web-tech/layout-paint-regressions-and-containment-decisions": "619",
    "web-tech/permit-browser-regression-investigation-project": "input-delay",
}
for path, expected in browser_diagnosis_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, expected, result.stdout)

react_rendering_lessons = [
    "web-tech/react-component-identity-and-keyed-draft-lifetime",
    "web-tech/react-derived-state-and-event-ownership",
    "web-tech/react-urgent-input-and-transition-work",
    "web-tech/react-hydration-and-stable-first-render",
]
for path in react_rendering_lessons:
    match = re.search(r'<pre><code class="language-jsx">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    subprocess.run([str(root / "node_modules/.bin/esbuild"), "--loader=jsx", "--format=esm"],
                   input=html.unescape(match.group(1)), text=True, check=True, capture_output=True)
project_path = "web-tech/react-permit-review-queue-state-project"
match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[project_path]["body"], re.S)
assert match, project_path
result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                        check=True, capture_output=True, text=True)
assert result.stdout.strip() == "null", result.stdout

vue_boundaries_lessons = [
    "web-tech/vue-source-state-computed-views-and-large-snapshots",
    "web-tech/vue-watch-cleanup-and-stale-request-ownership",
    "web-tech/vue-props-emits-and-keyed-editor-ownership",
    "web-tech/vue-server-rendering-and-hydration-stability",
]
for path in vue_boundaries_lessons:
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    subprocess.run(["node", "--check", "--input-type=module"], input=html.unescape(match.group(1)),
                   text=True, check=True, capture_output=True)
project_path = "web-tech/vue-permit-review-queue-project"
match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[project_path]["body"], re.S)
assert match, project_path
result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                        check=True, capture_output=True, text=True)
assert result.stdout.strip() == "false", result.stdout

svelte_boundaries_lessons = [
    "web-tech/svelte-runes-source-state-derived-views-and-effect-cleanup",
    "web-tech/svelte-props-callbacks-and-keyed-editor-ownership",
    "web-tech/sveltekit-form-actions-validation-and-mutation-replay",
    "web-tech/sveltekit-request-scoped-load-and-hydration-state",
]
for path in svelte_boundaries_lessons:
    match = re.search(r'<pre><code class="language-(?:svelte|typescript)">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    code = html.unescape(match.group(1))
    script = re.search(r'<script lang="ts">(.*?)</script>', code, re.S)
    parsed = script.group(1) if script else code
    subprocess.run([str(root / "node_modules/.bin/esbuild"), "--loader=ts", "--format=esm"],
                   input=parsed, text=True, check=True, capture_output=True)
project_path = "web-tech/svelte-permit-review-and-action-project"
match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[project_path]["body"], re.S)
assert match, project_path
result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                        check=True, capture_output=True, text=True)
assert result.stdout.strip() == "false", result.stdout

angular_boundaries_lessons = [
    "web-tech/angular-signal-sources-computed-views-and-effect-scope",
    "web-tech/angular-component-input-output-and-row-identity",
    "web-tech/angular-httpclient-streams-and-stale-detail-requests",
    "web-tech/angular-ssr-hydration-and-private-transfer-state",
]
for path in angular_boundaries_lessons:
    match = re.search(r'<pre><code class="language-typescript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    subprocess.run([str(root / "node_modules/.bin/esbuild"), "--loader=ts", "--format=esm"],
                   input=html.unescape(match.group(1)), text=True, check=True, capture_output=True)
project_path = "web-tech/angular-permit-operations-queue-project"
match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[project_path]["body"], re.S)
assert match, project_path
result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                        check=True, capture_output=True, text=True)
assert result.stdout.strip() == "false", result.stdout

nextjs_boundaries_lessons = [
    "web-tech/nextjs-server-client-component-and-data-boundary",
    "web-tech/nextjs-cache-scope-and-private-read-invalidation",
    "web-tech/nextjs-server-functions-validation-and-operation-identity",
    "web-tech/nextjs-streaming-suspense-and-error-recovery",
]
for path in nextjs_boundaries_lessons:
    match = re.search(r'<pre><code class="language-(tsx|typescript)">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    loader = "tsx" if match.group(1) == "tsx" else "ts"
    subprocess.run([str(root / "node_modules/.bin/esbuild"), "--loader=" + loader, "--format=esm"],
                   input=html.unescape(match.group(2)), text=True, check=True, capture_output=True)
project_path = "web-tech/nextjs-permit-delivery-and-cache-project"
match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[project_path]["body"], re.S)
assert match, project_path
result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                        check=True, capture_output=True, text=True)
assert result.stdout.strip() == "false", result.stdout

express_boundaries_lessons = [
    "web-tech/express-middleware-order-and-request-identity",
    "web-tech/express-five-async-errors-and-response-contracts",
    "web-tech/node-request-budgets-abort-and-event-loop-fairness",
    "web-tech/node-http-drain-readiness-and-graceful-shutdown",
]
for path in express_boundaries_lessons:
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    subprocess.run(["node", "--check", "--input-type=module"], input=html.unescape(match.group(1)),
                   text=True, check=True, capture_output=True)
project_path = "web-tech/express-permit-api-lifecycle-project"
match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[project_path]["body"], re.S)
assert match, project_path
result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                        check=True, capture_output=True, text=True)
assert result.stdout.strip() == "false", result.stdout

django_boundaries_lessons = [
    "web-tech/django-middleware-session-and-object-permissions",
    "web-tech/django-queryset-shape-prefetch-and-page-cost",
    "web-tech/django-form-csrf-atomic-approval-and-on-commit",
    "web-tech/django-asgi-async-view-and-sync-orm-boundary",
]
for path in django_boundaries_lessons:
    match = re.search(r'<pre><code class="language-python">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    ast.parse(html.unescape(match.group(1)))
project_path = "web-tech/django-permit-review-service-project"
match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[project_path]["body"], re.S)
assert match, project_path
result = subprocess.run(["node", "--input-type=module", "-e", html.unescape(match.group(1))],
                        check=True, capture_output=True, text=True)
assert result.stdout.strip() == "false", result.stdout

fastapi_boundaries_lessons = [
    "web-tech/fastapi-dependencies-and-object-authorization",
    "web-tech/fastapi-input-output-models-and-error-contracts",
    "web-tech/fastapi-async-sessions-and-transaction-ownership",
    "web-tech/fastapi-lifespan-background-work-and-delivery-state",
]
for path in fastapi_boundaries_lessons:
    match = re.search(r'<pre><code class="language-python">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    ast.parse(html.unescape(match.group(1)))
project_path = "web-tech/fastapi-permit-service-boundaries-project"
match = re.search(r'<pre><code class="language-python">(.*?)</code></pre>', by_path[project_path]["body"], re.S)
assert match, project_path
result = subprocess.run(["python3", "-c", html.unescape(match.group(1))],
                        check=True, capture_output=True, text=True)
assert result.stdout.strip() == "False", result.stdout

laravel_boundaries_lessons = [
    "web-tech/laravel-route-binding-policy-and-private-resource-scope",
    "web-tech/laravel-eloquent-loading-and-cursor-page-cost",
    "web-tech/laravel-form-request-transaction-and-approval-replay",
    "web-tech/laravel-after-commit-jobs-and-outbox-recovery",
]
for path in laravel_boundaries_lessons:
    match = re.search(r'<pre><code class="language-php">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    subprocess.run(["php", "-l"], input=html.unescape(match.group(1)),
                   text=True, check=True, capture_output=True)
project_path = "web-tech/laravel-permit-review-workflow-project"
match = re.search(r'<pre><code class="language-php">(.*?)</code></pre>', by_path[project_path]["body"], re.S)
assert match, project_path
result = subprocess.run(["php"], input=html.unescape(match.group(1)),
                        check=True, capture_output=True, text=True)
assert result.stdout.strip() == "false", result.stdout

flask_boundaries_lessons = [
    "web-tech/flask-request-context-and-object-authorization",
    "web-tech/flask-sqlalchemy-session-and-query-lifetime",
    "web-tech/flask-command-validation-and-transaction-replay",
    "web-tech/flask-async-views-and-durable-background-work",
]
for path in flask_boundaries_lessons:
    match = re.search(r'<pre><code class="language-python">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    ast.parse(html.unescape(match.group(1)))
project_path = "web-tech/flask-permit-service-boundaries-project"
match = re.search(r'<pre><code class="language-python">(.*?)</code></pre>', by_path[project_path]["body"], re.S)
assert match, project_path
result = subprocess.run(["python3", "-c", html.unescape(match.group(1))],
                        check=True, capture_output=True, text=True)
assert result.stdout.strip() == "False", result.stdout

rails_boundaries_lessons = [
    "web-tech/rails-controller-parameters-and-object-permission",
    "web-tech/rails-active-record-scope-eager-load-and-page-cost",
    "web-tech/rails-locking-transaction-and-command-replay",
    "web-tech/rails-active-job-after-commit-and-outbox-recovery",
]
for path in rails_boundaries_lessons:
    match = re.search(r'<pre><code class="language-ruby">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    subprocess.run(["ruby", "-c"], input=html.unescape(match.group(1)),
                   text=True, check=True, capture_output=True)
project_path = "web-tech/rails-permit-review-workflow-project"
match = re.search(r'<pre><code class="language-ruby">(.*?)</code></pre>', by_path[project_path]["body"], re.S)
assert match, project_path
result = subprocess.run(["ruby"], input=html.unescape(match.group(1)),
                        check=True, capture_output=True, text=True)
assert result.stdout.strip() == "false", result.stdout

cms_cases = {
    "web-tech/cms-public-content-projection-and-route-identity":
        'if (publicArticle({ ...editorialRecord, status: "draft" }) !== null) throw Error("draft exposed");\n'
        'if ("privateNote" in publicArticle(editorialRecord)) throw Error("private field exposed");',
    "web-tech/cms-draft-preview-authorization-and-cache-isolation":
        'if (previewDecision({ editorId: 81, articleId: 447, revision: 9, grants: [{ editorId: 47, articleId: 447 }] }).allowed) throw Error("wrong editor admitted");',
    "web-tech/cms-media-variants-alt-text-and-asset-ownership":
        'if (publicAsset({ ...inspectionDiagram, published: false }, "card") !== null) throw Error("draft media exposed");',
    "web-tech/cms-publish-events-cache-search-and-rollback":
        'if (searchDocument.version !== 9) throw Error("old event restored");',
}
for path, exercise in cms_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    subprocess.run(["node", "--input-type=module"], input=html.unescape(match.group(1)) + "\n" + exercise,
                   text=True, check=True, capture_output=True)
cms_project = "web-tech/cms-publication-reconciliation-project"
match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[cms_project]["body"], re.S)
assert match, cms_project
result = subprocess.run(["node", "--input-type=module"], input=html.unescape(match.group(1)),
                        text=True, check=True, capture_output=True)
assert result.stdout.strip() == "false\ntrue", result.stdout

spring_boot_lessons = {
    "web-tech/spring-boot-security-chain-and-object-permission": "@EnableMethodSecurity",
    "web-tech/spring-boot-mvc-validation-and-problem-contracts": "@Valid",
    "web-tech/spring-boot-jpa-scope-fetch-and-page-cost": "@EntityGraph",
    "web-tech/spring-boot-transaction-replay-and-outbox-handoff": "@Transactional",
}
for path, marker in spring_boot_lessons.items():
    match = re.search(r'<pre><code class="language-java">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match and marker in html.unescape(match.group(1)), path
spring_boot_project = "web-tech/spring-boot-permit-service-boundaries-project"
match = re.search(r'<pre><code class="language-java">(.*?)</code></pre>', by_path[spring_boot_project]["body"], re.S)
assert match, spring_boot_project
with tempfile.TemporaryDirectory() as directory:
    source = Path(directory) / "SpringPermitCheckpoint.java"
    source.write_text(html.unescape(match.group(1)))
    subprocess.run(["javac", str(source)], check=True, capture_output=True, text=True)
    result = subprocess.run(["java", "-cp", directory, "SpringPermitCheckpoint"],
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == "false\ntrue", result.stdout

security_cases = {
    "web-tech/federated-login-callback-boundary": (
        '\nconst state = "r".repeat(32);\n'
        'console.log(acceptCallbackBinding(state, { state, expiresAt: Date.now() + 1000 }));\n'
        'console.log(acceptCallbackBinding("s".repeat(32), { state, expiresAt: Date.now() + 1000 }));',
        "true\nfalse",
    ),
    "web-tech/outbound-url-and-ssrf-boundary": (
        '\nconsole.log(isApprovedImageLocation("https://images.inspection.example/photo/61"));\n'
        'console.log(isApprovedImageLocation("https://images.inspection.example.evil.test/photo/61"));\n'
        'console.log(isApprovedImageLocation("not a url"));',
        "true\nfalse\nfalse",
    ),
    "web-tech/signed-webhook-delivery-and-replay": (
        '\nconst rawBody = Buffer.from(\'{"eventId":584}\');\n'
        'const timestamp = "1900000000";\n'
        'const signedPayload = Buffer.concat([Buffer.from(`${timestamp}.`), rawBody]);\n'
        'const signature = createHmac("sha256", "rotation-key-47").update(signedPayload).digest("hex");\n'
        'console.log(hasValidWebhookSignature(rawBody, timestamp, signature, "rotation-key-47", 1900000010));\n'
        'console.log(hasValidWebhookSignature(rawBody, "1900000500", signature, "rotation-key-47", 1900000500));\n'
        'console.log(hasValidWebhookSignature(rawBody, timestamp, signature, "rotation-key-47", 1900001000));',
        "true\nfalse\nfalse",
    ),
}
for path, (exercise, expected) in security_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    code = html.unescape(match.group(1))
    result = subprocess.run(["node", "--input-type=module"], input=code + exercise,
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, result.stdout)

global_cases = {
    "web-tech/message-catalog-contracts-and-fallback": (
        '\nconsole.log(archivePrompt("en", "case 47"));\n'
        'console.log(archivePrompt("hi", "case 47"));\n'
        'console.log(archivePrompt("fr", "case 47"));',
        "Archive case 47?\ncase 47 को संग्रहित करें?\nArchive case 47?",
    ),
    "web-tech/localized-route-and-translation-release": (
        '\nconsole.log(pageFor("upload-photos", "hi"));\n'
        'console.log(pageFor("upload-photos", "fr"));\n'
        'console.log(pageFor("unknown", "en"));',
        "/hi/guides/photos\n/en/guides/upload-photos\nnull",
    ),
    "web-tech/currency-date-and-time-zone-presentation": (
        '\nconsole.log(localTime.includes("2026"));\n'
        'console.log(amount.includes("47.25"));',
        "true\ntrue",
    ),
}
for path, (exercise, expected) in global_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    code = html.unescape(match.group(1))
    result = subprocess.run(["node", "--input-type=module"], input=code + exercise,
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, result.stdout)

typed_path = "web-tech/typescript-and-runtime-api-boundaries"
typed_match = re.search(r'<pre><code class="language-typescript">(.*?)</code></pre>', by_path[typed_path]["body"], re.S)
assert typed_match, typed_path
typed_code = html.unescape(typed_match.group(1))
typed_exercise = '''
console.log(decodeCaseSummary({ caseId: 47, status: "open", reviewCount: 47 }).reviewCount);
try { decodeCaseSummary({ caseId: 47, status: "open", reviewCount: "47" }); }
catch { console.log("rejected"); }
try { decodeCaseSummary(null); }
catch { console.log("rejected"); }
try { decodeCaseSummary({ caseId: -47, status: "open", reviewCount: 1 }); }
catch { console.log("rejected"); }
try { decodeCaseSummary({ caseId: 47, status: "open", reviewCount: -1 }); }
catch { console.log("rejected"); }
'''
with tempfile.TemporaryDirectory() as temporary_directory:
    typed_file = Path(temporary_directory) / "case-boundary.ts"
    typed_file.write_text(typed_code + typed_exercise)
    subprocess.run([str(root / "node_modules/.bin/tsc"), "--strict", "--skipLibCheck",
                    "--target", "ES2022", "--outDir", temporary_directory, str(typed_file)],
                   check=True, capture_output=True, text=True)
    typed_result = subprocess.run(["node", str(Path(temporary_directory) / "case-boundary.js")],
                                  check=True, capture_output=True, text=True)
    assert typed_result.stdout.strip() == "47\nrejected\nrejected\nrejected\nrejected", typed_result.stdout

platform_cases = {
    "web-tech/dom-sinks-and-trusted-content": (
        'const noteTarget = { textContent: "", innerHTML: "unchanged" };\n'
        'globalThis.document = { querySelector: () => noteTarget };\n',
        '\nconsole.log(noteTarget.textContent);\nconsole.log(noteTarget.innerHTML);',
        "Damaged <pipe> at level 47\nunchanged",
    ),
    "web-tech/telemetry-minimization-and-retention": (
        "",
        '\nconsole.log(operationEvent("decode_failure", "req-47", "release-29").event);\n'
        'try { operationEvent("token_dump", "req-47", "release-29"); }\n'
        'catch { console.log("rejected"); }',
        "decode_failure\nrejected",
    ),
}
for path, (setup, exercise, expected) in platform_cases.items():
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    code = html.unescape(match.group(1))
    result = subprocess.run(["node", "--input-type=module"], input=setup + code + exercise,
                            check=True, capture_output=True, text=True)
    assert result.stdout.strip() == expected, (path, result.stdout)

for quiz in quiz_entries:
    questions = quiz["data"]["questions"]
    assert len(questions) == 12, quiz["path"]
    assert len({item["prompt"] for item in questions}) == 12, quiz["path"]
    for item in questions:
        assert len(item["options"]) == 3, quiz["path"]
        assert len(set(item["options"])) == 3, quiz["path"]
        assert 0 <= item["answer"] < 3, quiz["path"]
        assert len(item["explanation"]) >= 70, (quiz["path"], item["prompt"])

native_node_lessons = by_path["web-tech/node-native-http-and-runtime-boundaries"]["data"]["modules"][0]["lessons"]
php_runtime_lessons = by_path["web-tech/php-request-session-and-persistence-boundaries"]["data"]["modules"][0]["lessons"]
for path in native_node_lessons:
    match = re.search(r'<pre><code class="language-javascript">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    subprocess.run(["node", "--input-type=module", "--check"], input=html.unescape(match.group(1)),
                   check=True, capture_output=True, text=True)
for path in php_runtime_lessons:
    match = re.search(r'<pre><code class="language-php">(.*?)</code></pre>', by_path[path]["body"], re.S)
    assert match, path
    subprocess.run(["php", "-l"], input=html.unescape(match.group(1)),
                   check=True, capture_output=True, text=True)

for path in ("quizzes/web-development-django-request-persistence",
             "quizzes/web-development-fastapi-contract-resources",
             "quizzes/web-development-laravel-policy-query-queue",
             "quizzes/web-development-flask-context-service-boundaries",
             "quizzes/web-development-rails-request-record-job",
             "quizzes/web-development-cms-publication-contracts",
             "quizzes/web-development-spring-boot-service-contracts",
             "quizzes/web-development-node-runtime-contracts",
             "quizzes/web-development-php-request-contracts"):
    answers = [item["answer"] for item in by_path[path]["data"]["questions"]]
    assert [answers.count(position) for position in range(3)] == [4, 4, 4], path

report = {"web_development_routes": len(web_entries), "broad_hubs": len(broad_hubs),
          "technical_lessons": len(technical),
          "deepened_lessons": len(deepened) + len(foundation), "projects": len(projects),
          "quiz_routes": len(quiz_entries), "questions": sum(len(quiz["data"]["questions"]) for quiz in quiz_entries),
          "runnable_examples_checked": ran, "security_boundary_examples_checked": len(security_cases),
          "global_delivery_examples_checked": len(global_cases),
          "platform_examples_checked": 1 + len(platform_cases),
          "search_quality_examples_checked": len(search_quality_cases),
          "layout_css_examples_parsed": len(layout_css_paths),
          "browser_runtime_examples_checked": len(runtime_cases),
          "api_mutation_examples_checked": len(api_mutation_cases),
          "rendering_form_examples_checked": len(rendering_form_cases),
          "browser_form_examples_syntax_checked": 2,
          "navigation_delivery_examples_checked": len(navigation_delivery_cases),
          "streams_interactions_examples_checked": len(streams_interactions_cases),
          "operations_sync_examples_checked": len(operations_sync_cases),
          "authorization_lifecycle_examples_checked": len(authorization_lifecycle_cases),
          "browser_capability_examples_checked": len(browser_capability_cases),
          "accessible_privacy_examples_checked": len(accessible_privacy_cases),
          "push_notification_examples_checked": len(push_notification_cases),
          "passkey_checkout_examples_checked": len(passkey_checkout_cases),
          "file_email_examples_checked": len(file_email_cases),
          "release_graphql_examples_checked": len(release_graphql_cases),
          "browser_compute_peer_examples_checked": len(browser_compute_peer_cases),
          "motion_region_examples_checked": len(motion_region_cases),
          "graphics_editing_examples_checked": len(graphics_editing_cases),
          "embeds_build_examples_checked": len(embeds_build_cases),
          "offline_crypto_examples_checked": len(offline_crypto_cases),
          "components_compatibility_examples_checked": len(components_compatibility_cases),
          "jobs_abuse_examples_checked": len(jobs_abuse_cases),
          "model_app_examples_checked": len(model_app_cases),
          "media_playback_examples_checked": len(media_playback_cases),
          "extension_geospatial_examples_checked": len(extension_geo_cases),
          "federation_examples_checked": len(federation_cases),
          "api_evolution_examples_checked": len(api_evolution_cases),
          "edge_origin_examples_checked": len(edge_origin_cases),
          "realtime_examples_checked": len(realtime_cases),
          "network_examples_checked": len(network_cases),
          "database_operations_examples_checked": len(database_operations_cases),
          "application_cache_examples_checked": len(application_cache_cases),
          "ingress_examples_checked": len(ingress_cases),
          "browser_diagnosis_examples_checked": len(browser_diagnosis_cases),
          "react_jsx_examples_parsed": len(react_rendering_lessons),
          "react_project_example_checked": 1,
          "vue_examples_syntax_checked": len(vue_boundaries_lessons),
          "vue_project_example_checked": 1,
          "angular_typescript_examples_parsed": len(angular_boundaries_lessons),
          "angular_project_example_checked": 1,
          "svelte_script_examples_parsed": len(svelte_boundaries_lessons),
          "svelte_project_example_checked": 1,
          "nextjs_script_examples_parsed": len(nextjs_boundaries_lessons),
          "nextjs_project_example_checked": 1,
          "express_examples_syntax_checked": len(express_boundaries_lessons),
          "express_project_example_checked": 1,
          "django_python_examples_parsed": len(django_boundaries_lessons),
          "django_project_example_checked": 1,
          "fastapi_python_examples_parsed": len(fastapi_boundaries_lessons),
          "fastapi_project_example_checked": 1,
          "laravel_php_examples_syntax_checked": len(laravel_boundaries_lessons),
          "laravel_project_example_checked": 1,
          "flask_python_examples_parsed": len(flask_boundaries_lessons),
          "flask_project_example_checked": 1,
          "rails_ruby_examples_syntax_checked": len(rails_boundaries_lessons),
          "rails_project_example_checked": 1,
          "cms_javascript_examples_checked": len(cms_cases),
          "cms_project_example_checked": 1,
          "spring_boot_snippets_checked": len(spring_boot_lessons),
          "spring_boot_project_example_checked": 1,
          "native_node_snippets_checked": len(native_node_lessons),
          "php_runtime_snippets_checked": len(php_runtime_lessons),
          "runtime_project_checkpoints_checked": 2,
          "broken_internal_links": 0, "unreachable_routes": 0}
output = root / "work/web-development-validation.json"
output.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report))
