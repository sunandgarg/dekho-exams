=== Dekhoexams School Content ===
Contributors: dekhoexams
Requires at least: 6.0
Requires PHP: 8.0
Stable tag: 1.0.0
License: GPLv2 or later

Publishes school lesson text from WordPress to the Dekhoexams frontend.

Upload the dekhoexams-school-content folder as a ZIP in WordPress > Plugins > Add New > Upload Plugin, then activate it. Add a School lesson with the stable resource ID shown in the frontend catalog (pp-0001 through pp-0014). Fill every text field and publish. Drafts are never returned by the public API.

Verify https://cms.pencil2pen.com/wp-json/dekhoexams/v1/lesson?id=pp-0001 returns the published lesson. Set SCHOOL_WORDPRESS_URL=https://cms.pencil2pen.com on the Cloudflare Worker. The frontend keeps its local lesson when the endpoint is unavailable. This plugin does not implement learner accounts, server-side attempts, or question editing.
