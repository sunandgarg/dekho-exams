import { Children, isValidElement, useRef, useState, type ReactNode } from "react";
import { isPublicPath } from "@/lib/features";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { toJsxRuntime } from "hast-util-to-jsx-runtime";
import { Fragment, jsx, jsxs } from "react/jsx-runtime";
import { parseTutorialHtml } from "@/lib/tutorial-html";
import { fromHtml } from "hast-util-from-html";
import hljs from "highlight.js/lib/core";
import java from "highlight.js/lib/languages/java";
import javascript from "highlight.js/lib/languages/javascript";
import python from "highlight.js/lib/languages/python";
import css from "highlight.js/lib/languages/css";
import xml from "highlight.js/lib/languages/xml";
import cpp from "highlight.js/lib/languages/cpp";
import { Link } from "@tanstack/react-router";

hljs.registerLanguage("java", java);
hljs.registerLanguage("javascript", javascript);
hljs.registerLanguage("python", python);
hljs.registerLanguage("css", css);
hljs.registerLanguage("html", xml);
hljs.registerLanguage("cpp", cpp);

function HighlightedCode({
  children,
  className,
}: {
  children?: ReactNode;
  className?: string | undefined;
}) {
  const language = className?.replace(/^language-/, "");
  const text = typeof children === "string" ? children : undefined;
  if (!text || !language || !hljs.getLanguage(language))
    return <code className={className}>{children}</code>;
  const result = hljs.highlight(text, { language, ignoreIllegals: true });
  return (
    <code className={className}>
      {toJsxRuntime(fromHtml(result.value, { fragment: true }), { Fragment, jsx, jsxs })}
    </code>
  );
}

/** Supports legacy Markdown and a strict allowlist for editor-written tutorial HTML. */
export function Markdown({ source }: { source: string }) {
  if (!source.trim()) return null;
  const html = /^\s*<(?:p|h2|h3|ul|pre)\b/i.test(source);
  return (
    <div className="article-content">
      {html ? (
        toJsxRuntime(parseTutorialHtml(source), {
          Fragment,
          jsx,
          jsxs,
          components: {
            pre: CodeBlock,
            code: HighlightedCode,
            a: ({ href, children }) =>
              href ? (
                <Link to="/$" params={{ _splat: href.replace(/^\//, "") }}>
                  {children}
                </Link>
              ) : (
                <>{children}</>
              ),
          },
        })
      ) : (
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            a: ({ href = "", children }) =>
              !isPublicPath(href) ? null : href.startsWith("/") && !href.startsWith("/fonts/") ? (
                <Link to="/$" params={{ _splat: href.replace(/^\//, "") }}>
                  {children}
                </Link>
              ) : (
                <a href={href} target="_blank" rel="noopener noreferrer">
                  {children}
                </a>
              ),
            pre: ({ children }) => <CodeBlock>{children}</CodeBlock>,
            code: HighlightedCode,
            img: ({ src, alt }) =>
              !src || !src.startsWith("/") || src.startsWith("//") ? (
                <p className="text-sm">
                  External illustration not loaded.{" "}
                  {alt || "An image description must be supplied by the editor."}
                </p>
              ) : (
                <img
                  src={src}
                  alt={alt || "Illustration (description pending editorial review)"}
                  loading="lazy"
                  className="max-w-full"
                />
              ),
            table: ({ children }) => (
              <div className="overflow-x-auto">
                <table>{children}</table>
              </div>
            ),
          }}
        >
          {source}
        </ReactMarkdown>
      )}
    </div>
  );
}

function CodeBlock({ children }: { children: ReactNode }) {
  const code = Children.toArray(children).find((child) => isValidElement(child));
  const language = isValidElement<{ className?: string }>(code)
    ? code.props.className?.replace(/^language-/, "")
    : undefined;
  const label =
    language === "text" ? "Output" : language ? (language === "java" ? "Java" : language) : "Code";
  const ref = useRef<HTMLPreElement>(null);
  const [notice, setNotice] = useState("");
  return (
    <div className="tutorial-code-block min-w-0">
      <div className="tutorial-code-toolbar">
        <span className="text-xs font-semibold">{label}</span>
        <button
          type="button"
          className="border px-3 py-1 text-xs font-semibold"
          onClick={async () => {
            try {
              await navigator.clipboard.writeText(ref.current?.textContent ?? "");
              setNotice("Code copied");
            } catch {
              setNotice("Copy unavailable. Select the code to copy it manually.");
            }
          }}
        >
          Copy code
        </button>
        <span role="status" className="ml-3 text-xs">
          {notice}
        </span>
      </div>
      <pre ref={ref}>{children}</pre>
    </div>
  );
}
