# Cloudflare, Lightsail and S3

Cloudflare serves the public domain, caches public exam pages and fetches PDFs
and figures directly from private S3 using a dedicated read-only identity.
Node on Lightsail renders pages. The managed MySQL database stores versioned
copies of the published archive shards and CMS snapshot. The release's school
catalog and templates stay in the app. Publishing requires a new release ID.
Reconcile any edits made only in WordPress before promoting a release.

## Provision in Mumbai

Set AWS_PROFILE and AWS_REGION=ap-south-1. Verify the AWS account with
`aws sts get-caller-identity`. Check existing resources and select an available
Mumbai zone, an active 1 GB Linux IPv4 bundle and the active default MySQL
blueprint from the Lightsail APIs. The stack uses the standard 1 GB MySQL
plan, private networking, and automated DB backups. Use an existing Lightsail
SSH key pair or import a project-specific **public** SSH key. From the repository root:

```sh
aws cloudformation deploy --stack-name dekhoexams --template-file deploy/lightsail/stack.yaml \
  --capabilities CAPABILITY_IAM --parameter-overrides Zone="$ZONE" InstanceBundle="$BUNDLE" \
  DatabaseBlueprint="$MYSQL_BLUEPRINT" AdminCidr="$ADMIN_IPV4/32" KeyPairName="$KEY_NAME"
aws cloudformation describe-stacks --stack-name dekhoexams --query 'Stacks[0].Outputs'
```

The stack retains the database and S3 bucket on deletion. They continue to
incur charges until intentionally removed.

## Publish media and content

Run `npm ci` and `npm run build:node` on a build machine using Node 26. This
restores and checks the PDF releases and generates the sitemaps. Use the
MediaBucket output for BUCKET. These commands preserve existing objects.

```sh
aws s3 sync public/jee-papers "s3://$BUCKET/jee-papers" --only-show-errors --no-follow-symlinks
aws s3 sync public/jee-figures "s3://$BUCKET/jee-figures" --only-show-errors --no-follow-symlinks
```

Install Node 26, npm and Caddy on the Ubuntu instance. Copy package.json,
package-lock.json, dist/, server/, scripts/import-lightsail.mjs and public/
(exclude jee-papers and jee-figures) to /srv/dekhoexams. Install runtime
dependencies there with `npm ci --omit=dev`. Build off the 1 GB server.
Set a DNS-only A record for origin.dekhoexams.com to OriginIP so Caddy can
obtain a TLS certificate. Keep public site DNS on the existing Worker.

From the Lightsail instance, obtain the DB endpoint and trusted AWS RDS CA
bundle. Set MYSQL_HOST, MYSQL_DATABASE=dekhoexams, MYSQL_CA_FILE, MYSQL_USER,
MYSQL_PASSWORD and ARCHIVE_RELEASE (the release commit) for the importer.
Use a writer for the import and execute `node scripts/import-lightsail.mjs`.
This imports all archive files in one transaction. Allocate a new release ID
when content changes. Grant a separate runtime DB user SELECT on
dekhoexams.published_assets and put its settings and the same release ID in
/etc/dekhoexams/app.env, owned by root with mode 0600. Use the service file
with a dedicated dekhoexams OS user and Node at /usr/local/bin/node.
Start the service only after import succeeds.

Set ORIGIN_HOST and a random ORIGIN_KEY for Caddy, install the supplied
Caddyfile, and reload Caddy. Keep credentials out of source control and logs.
The origin requires the shared key and only Caddy connects to Node on loopback.

## Stage and promote

Create a dedicated access key for the stack's ReaderUser. It can read only
the two S3 media prefixes. Store the ID and secret as Cloudflare Worker
secrets S3_KEY_ID and S3_SECRET. Set the ORIGIN_KEY Worker secret to the same
value as Caddy. For a fresh staging Worker, deploy the bundle and immediately
configure secrets before testing. Set APP_ORIGIN, MEDIA_BUCKET and AWS_REGION
as Worker variables on every deployment.

```sh
npx wrangler deploy --config deploy/lightsail/wrangler.jsonc \
  --var APP_ORIGIN:https://origin.dekhoexams.com --var MEDIA_BUCKET:"$BUCKET" --var AWS_REGION:ap-south-1
npx wrangler secret put S3_KEY_ID --config deploy/lightsail/wrangler.jsonc
npx wrangler secret put S3_SECRET --config deploy/lightsail/wrangler.jsonc
npx wrangler secret put ORIGIN_KEY --config deploy/lightsail/wrangler.jsonc
```

Run `TEST_ORIGIN=https://<staging-worker> node scripts/test-node.mjs`. Check
both exam archives, a figure, sitemap.xml, a PDF range request (206), and
that direct unauthenticated origin requests return 403. For production, record
the current dekhoexams-frontend version for rollback, configure the same three
secrets for that Worker, then deploy with the same variables and
`--name dekhoexams-frontend`. Verify HTTPS, canonical URLs, archive and media
requests via dekhoexams.com. Roll back to the recorded Worker version if the
production checks fail.
