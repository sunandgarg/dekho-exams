import { useId } from "react";

/** Original book-and-notes artwork for the local design study. */
export function TopicIllustration({ kind = "java" }: { kind?: "java" | "ai" | "web" | "logic" }) {
  const id = useId().replace(/:/g, "");
  const colour =
    kind === "ai"
      ? "#b66a87"
      : kind === "web"
        ? "#608eb0"
        : kind === "logic"
          ? "#c38b44"
          : "#4b8066";
  const label = kind === "ai" ? "AI" : kind === "web" ? "WEB" : kind === "logic" ? "DSA" : "JAVA";
  return (
    <svg viewBox="0 0 460 330" aria-hidden="true" className="topic-illustration">
      <defs>
        <pattern id={id} width="15" height="15" patternUnits="userSpaceOnUse">
          <path d="M 15 0 L 0 0 0 15" fill="none" stroke="#ddd6c9" strokeWidth=".5" />
        </pattern>
      </defs>
      <ellipse cx="235" cy="292" rx="156" ry="15" fill="#26342a" opacity=".08" />
      <g transform="translate(44 48) rotate(-9 80 105)">
        <rect x="0" y="0" width="146" height="186" rx="12" fill="#fffdfa" stroke="#d4ccbc" />
        <rect x="0" y="0" width="146" height="186" rx="12" fill={`url(#${id})`} />
        <rect x="16" y="20" width="52" height="8" rx="3" fill="#e6bfca" />
        <path
          d="M22 62h102M22 80h85M22 98h98"
          stroke="#afa899"
          strokeWidth="3"
          strokeLinecap="round"
        />
        <rect x="22" y="125" width="27" height="28" rx="6" fill="#dfece2" stroke="#55876a" />
        <rect x="96" y="125" width="27" height="28" rx="6" fill="#f3dfc4" stroke="#b88a51" />
        <path d="M53 139h35m-7-6 7 6-7 6" fill="none" stroke="#55876a" strokeWidth="2" />
      </g>
      <g transform="translate(160 27) rotate(8 93 116)">
        <path d="M14 15h153a11 11 0 0 1 11 11v219H14z" fill="#f0e5d2" stroke="#b8ad99" />
        <path d="M22 233h153M22 240h153" stroke="#ccc0aa" />
        <rect x="0" y="0" width="178" height="232" rx="10" fill={colour} />
        <path d="M15 0v232" stroke="#173d2c" opacity=".22" strokeWidth="3" />
        <rect x="30" y="27" width="118" height="150" rx="3" fill="#fff9eb" />
        <text x="44" y="49" fontSize="8" fontFamily="sans-serif" letterSpacing="1.2" fill={colour}>
          DEKHOEXAMS / NOTES
        </text>
        <text
          x="89"
          y="114"
          textAnchor="middle"
          fontFamily="Georgia, serif"
          fontWeight="bold"
          fontSize={label.length > 3 ? 33 : 47}
          fill={colour}
        >
          {label}
        </text>
        <path d="M46 137h87M46 149h66" stroke={colour} strokeWidth="2" opacity=".5" />
        <text x="31" y="206" fontSize="8" letterSpacing="1.2" fontFamily="sans-serif" fill="#fff9eb">
          READ. TRY. REPEAT.
        </text>
      </g>
      <g transform="translate(299 181) rotate(-7)">
        <rect width="125" height="71" rx="9" fill="#fbecce" stroke="#d4b47c" />
        <text
          x="14"
          y="27"
          fontFamily="Georgia, serif"
          fontSize="11"
          fontWeight="bold"
          fill="#694723"
        >
          one idea at a time
        </text>
        <path d="M15 45h75M15 54h55" stroke="#b69152" strokeWidth="2" strokeLinecap="round" />
      </g>
      <g transform="translate(354 40) rotate(24)">
        <path d="M0 0h12v105L6 120 0 105z" fill="#e7b668" stroke="#ae8243" />
        <path d="M0 105h12l-6 15z" fill="#f1dfc0" />
        <path d="M4 115h4l-2 5z" fill="#493b34" />
        <rect width="12" height="14" rx="3" fill="#d79ba5" />
        <path d="M6 16v87" stroke="#f5cd88" strokeWidth="3" />
      </g>
    </svg>
  );
}
