const logos: Record<string, string[]> = {
  "ai-tools/chatgpt-codex": ["openai"],
  "ai-tools/claude-claude-code": ["claude"],
  "web-tech/web-technology": ["html5"],
  "python/python-programming-language-tutorial": ["python"],
  "java/java": ["java"],
  "javascript/javascript-tutorial": ["javascript"],
  "html/html-tutorial": ["html5"],
  "css/css-tutorial": ["css3"],
  "c/c-programming-language": ["c"],
  "cpp/c-plus-plus": ["cplusplus"],
  "linux-unix/linux-tutorial": ["linux"],
  "devops/devops-tutorial": ["docker"],
  "tutorials/programming-language-tutorials": ["javascript"],
  "websites-apps/software-and-tools-a-to-z-list": ["git"],
};

// Broad subjects use original topic diagrams, not a vendor's trademark.
function diagram(path: string) {
  if (path.startsWith("prompt-engineering/"))
    return (
      <>
        <rect x="5" y="7" width="38" height="28" rx="4" />
        <path d="M12 15h20M12 22h13M12 29h17M24 35v7M18 42h12M34 13l2 2-2 2" />
      </>
    );
  if (path.startsWith("spring/"))
    return (
      <>
        <rect x="4" y="16" width="13" height="16" rx="2" />
        <rect x="31" y="16" width="13" height="16" rx="2" />
        <path d="M17 24h14M22 19l5 5-5 5M10 10V5h28v5M10 38v5h28v-5" />
      </>
    );
  if (/programming-language/.test(path))
    return (
      <>
        <path d="M15 12 3 24l12 12M33 12l12 12-12 12M28 7 20 41" />
      </>
    );
  if (/database|sql|dbms/.test(path))
    return (
      <>
        <ellipse cx="24" cy="11" rx="15" ry="6" />
        <path d="M9 11v25c0 8 30 8 30 0V11M9 23c0 8 30 8 30 0" />
      </>
    );
  if (/interview/.test(path))
    return (
      <>
        <path d="M5 8h29v21H17l-8 7v-7H5zM20 35h19l5 5V19h-5" />
        <path d="M12 15h15M12 22h10" />
      </>
    );
  if (/machine|data-science|ai-ml/.test(path))
    return (
      <>
        <circle cx="24" cy="24" r="9" />
        <path d="M24 4v11M24 33v11M4 24h11M33 24h11M10 10l8 8M30 30l8 8M10 38l8-8M30 18l8-8" />
      </>
    );
  if (/system-design/.test(path))
    return (
      <>
        <rect x="16" y="4" width="16" height="10" rx="1" />
        <rect x="3" y="33" width="16" height="10" rx="1" />
        <rect x="29" y="33" width="16" height="10" rx="1" />
        <path d="M24 14v10H11v9M24 24h13v9" />
      </>
    );
  if (/computer-science/.test(path))
    return (
      <>
        <rect x="12" y="12" width="24" height="24" rx="2" />
        <path d="M18 4v8M30 4v8M18 36v8M30 36v8M4 18h8M4 30h8M36 18h8M36 30h8M19 19h10v10H19z" />
      </>
    );
  return (
    <>
      <circle cx="24" cy="8" r="4" />
      <circle cx="10" cy="36" r="4" />
      <circle cx="38" cy="36" r="4" />
      <path d="M24 12v10H10v10M24 22h14v10M18 39h12" />
    </>
  );
}

export function TopicMark({ path, compact = false }: { path: string; compact?: boolean }) {
  const marks = logos[path];
  return (
    <span
      aria-hidden="true"
      className={`inline-flex shrink-0 items-center justify-center ${compact ? "gap-1" : "gap-2"}`}
    >
      {marks?.map((name) => (
        <span
          key={name}
          className={`inline-flex items-center justify-center rounded-md bg-white ${compact ? "size-6 p-1" : "size-12 p-2 sm:size-14"}`}
        >
          <img
            src={`/logos/${name}.svg`}
            alt=""
            width="40"
            height="40"
            className="h-full w-full object-contain"
          />
        </span>
      )) ?? (
        <svg
          width={compact ? 20 : 48}
          height={compact ? 20 : 48}
          viewBox="0 0 48 48"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          {diagram(path)}
        </svg>
      )}
    </span>
  );
}
