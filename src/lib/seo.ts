import type { Entry, EntryListItem } from "./content-types";
import { isPublicEntryType, isPublicPath } from "./features";

const DEFAULT_SITE_URL = "https://dekhoexams.com";

export function validatedSiteOrigin(value?: string): string {
  const url = new URL(value?.trim() || DEFAULT_SITE_URL);
  if (
    url.protocol !== "https:" ||
    url.username ||
    url.password ||
    url.search ||
    url.hash ||
    url.pathname !== "/"
  ) {
    throw new Error(
      "VITE_SITE_URL must be an HTTPS origin without credentials, path, query or fragment.",
    );
  }
  return url.origin;
}

export const SITE_ORIGIN = validatedSiteOrigin(import.meta.env["VITE_SITE_URL"]);
// Preview and unconfigured builds stay out of public search until editorial launch.
export const IS_PREVIEW = import.meta.env["VITE_PREVIEW_MODE"] !== "false";
export const SITE_IMAGE = `${SITE_ORIGIN}/dekhoexams-social.png`;
const SITE_LOGO = `${SITE_ORIGIN}/dekhoexams-icon-192.png`;

export function normalizedContentPath(path: string): string {
  const clean = path.split(/[?#]/, 1)[0]!.replace(/^\/+|\/+$/g, "");
  // The final segment in a paper can be a case-sensitive published question ID.
  return /^past-years\/year-wise\/jee\/(?:jee-main|jee-advanced)\/[^/]+\/[^/]+$/.test(clean) ? clean : clean.toLowerCase();
}

export function isUtilityPath(path: string): boolean {
  return /^(?:my-study|admin|auth|login|signup|forgot-password|reset-password|account|dashboard|search|site-map|(?:java|learning)-coverage\.html|checkout|learn)(?:\/|$)|\/(?:attempt|result|apply|participate|leaderboard)$/.test(
    normalizedContentPath(path),
  );
}

export function canonicalUrl(path: string, page?: number): string {
  const clean = normalizedContentPath(path);
  const url = new URL(clean ? `/${clean}` : "/", SITE_ORIGIN);
  if (page && page > 1) url.searchParams.set("page", String(page));
  return url.href;
}

type SeoEntry = Pick<EntryListItem, "type" | "path" | "status" | "data">;
export function isSeoReady(entry: SeoEntry): boolean {
  const data = entry.data;
  return (
    entry.status === "published" &&
    isPublicEntryType(entry.type) &&
    isPublicPath(entry.path) &&
    !isUtilityPath(entry.path) &&
    !!data &&
    !Array.isArray(data) &&
    typeof data === "object" &&
    data["seo_ready"] === true
  );
}

function validDate(value: string | null | undefined): string | undefined {
  return value && Number.isFinite(Date.parse(value)) ? new Date(value).toISOString() : undefined;
}

export type SeoMetadata = Pick<
  Entry,
  "path" | "type" | "title" | "summary" | "data" | "status" | "published_at" | "updated_at"
>;

export function schemaForEntry(entry: SeoMetadata): Record<string, unknown>[] {
  if (!isSeoReady(entry)) return [];
  const url = canonicalUrl(entry.path);
  const publisher = {
    "@type": "Organization",
    "@id": `${SITE_ORIGIN}/#organization`,
    name: "Dekhoexams",
    url: SITE_ORIGIN,
    logo: { "@type": "ImageObject", url: SITE_LOGO },
  };
  const type =
    entry.type === "article"
      ? "Article"
      : entry.type === "subject" || entry.type === "category"
        ? "CollectionPage"
        : entry.type === "quiz"
          ? "LearningResource"
          : "WebPage";
  const page: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": type,
    "@id": `${url}#content`,
    url,
    name: entry.title,
    description: entry.summary,
    inLanguage: "en",
    publisher,
  };
  if (entry.type === "article") {
    page["headline"] = entry.title;
    page["mainEntityOfPage"] = url;
    page["author"] = {
      "@type": "Organization",
      name: "Dekhoexams Editorial",
    };
    const published = validDate(entry.published_at);
    const modified = validDate(entry.updated_at);
    if (published) page["datePublished"] = published;
    if (modified) page["dateModified"] = modified;
  }
  if (entry.type === "quiz") page["learningResourceType"] = "Self-check quiz";
  const data =
    entry.data && typeof entry.data === "object" && !Array.isArray(entry.data) ? entry.data : {};
  const section =
    typeof data["section_path"] === "string" ? normalizedContentPath(data["section_path"]) : "";
  const tabs = Array.isArray(data["resource_tabs"]) ? data["resource_tabs"] : [];
  const tab = tabs.find(
    (item) => item && typeof item === "object" && !Array.isArray(item) && item["path"] === section,
  );
  const sectionName =
    tab && typeof tab === "object" && !Array.isArray(tab) && typeof tab["title"] === "string"
      ? tab["title"]
      : undefined;
  const items = [{ "@type": "ListItem", position: 1, name: "Home", item: canonicalUrl("") }];
  if (section && section !== entry.path && sectionName)
    items.push({
      "@type": "ListItem",
      position: items.length + 1,
      name: sectionName,
      item: canonicalUrl(section),
    });
  items.push({ "@type": "ListItem", position: items.length + 1, name: entry.title, item: url });
  return [
    page,
    { "@context": "https://schema.org", "@type": "BreadcrumbList", itemListElement: items },
  ];
}

export function seoHead({
  title,
  description,
  path = "",
  noindex = false,
  page,
  schema = [],
}: {
  title: string;
  description: string;
  path?: string;
  noindex?: boolean;
  page?: number | undefined;
  schema?: Record<string, unknown>[];
}) {
  const canonical = canonicalUrl(path, page);
  const excluded = IS_PREVIEW || noindex || isUtilityPath(path);
  return {
    meta: [
      { title: `${title} — Dekhoexams` },
      { name: "description", content: description },
      { name: "robots", content: excluded ? "noindex,follow" : "index,follow" },
      { property: "og:title", content: `${title} — Dekhoexams` },
      { property: "og:description", content: description },
      { property: "og:url", content: canonical },
      { property: "og:image", content: SITE_IMAGE },
      { property: "og:image:width", content: "1200" },
      { property: "og:image:height", content: "630" },
      { property: "og:image:alt", content: "Dekhoexams learning platform" },
      {
        property: "og:type",
        content: schema.some((item) => item["@type"] === "Article") ? "article" : "website",
      },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "twitter:image", content: SITE_IMAGE },
    ],
    links: [{ rel: "canonical", href: canonical }],
    scripts: schema.map((item) => ({
      type: "application/ld+json",
      children: JSON.stringify(item).replace(/</g, "\\u003c"),
    })),
  };
}

export function homeSchema(): Record<string, unknown>[] {
  return [
    {
      "@context": "https://schema.org",
      "@type": "Organization",
      "@id": `${SITE_ORIGIN}/#organization`,
      name: "Dekhoexams",
      url: SITE_ORIGIN,
      logo: SITE_LOGO,
    },
    {
      "@context": "https://schema.org",
      "@type": "WebSite",
      "@id": `${SITE_ORIGIN}/#website`,
      name: "Dekhoexams",
      url: SITE_ORIGIN,
      inLanguage: "en",
      publisher: { "@id": `${SITE_ORIGIN}/#organization` },
    },
  ];
}
