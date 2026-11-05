import type { Nodes, Root } from "hast";
import { fromHtml } from "hast-util-from-html";
import { sanitize, type Schema } from "hast-util-sanitize";

export const tutorialHtmlSchema: Schema = {
  tagNames: ["p", "h2", "h3", "ul", "li", "strong", "pre", "code", "a"],
  attributes: { code: [["className", /^language-[a-z0-9-]+$/]], a: ["href"] },
  strip: ["script", "style", "iframe", "object", "embed"],
};

/** Parse HTML directly so blank lines inside preformatted code remain literal. */
export function parseTutorialHtml(source: string) {
  const tree = sanitize(fromHtml(source, { fragment: true }), tutorialHtmlSchema) as Root;
  // Tutorial links stay within this site. Discard external, protocol-relative,
  // escaped and archived course URLs before they reach the router.
  function check(node: Nodes) {
    if (node.type === "element" && node.tagName === "a") {
      const href = String(node.properties.href ?? "");
      if (
        !/^\/(?!\/)[a-z0-9/-]+(?:#[a-z0-9-]+)?$/i.test(href) ||
        /^\/courses(?:\/|$)/i.test(href)
      ) {
        delete node.properties.href;
      }
    }
    if ("children" in node) node.children.forEach(check);
  }
  check(tree);
  return tree;
}
