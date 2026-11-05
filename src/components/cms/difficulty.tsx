const levels = ["Easy", "Medium", "Hard"];

function tone(value?: string | null) {
  const level = value?.toLowerCase();
  return level === "easy" || level === "beginner"
    ? "easy"
    : level === "hard" || level === "advanced"
      ? "hard"
      : level === "medium" || level === "intermediate"
        ? "medium"
        : "neutral";
}

export function DifficultyBadge({ value }: { value?: string | null }) {
  if (!value) return null;
  return (
    <span className={`difficulty-pill difficulty-${tone(value)}`} data-difficulty={value}>
      {value}
    </span>
  );
}

export function DifficultyFilter({
  value,
  onChange,
}: {
  value?: string | undefined;
  onChange: (value: string) => void;
}) {
  return (
    <fieldset>
      <legend className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
        Difficulty
      </legend>
      <div className="difficulty-options mt-2">
        {["All", ...levels].map((level) => (
          <button
            type="button"
            key={level}
            className={`difficulty-pill difficulty-${tone(level)}`}
            aria-pressed={level === "All" ? !value : value === level}
            onClick={() => onChange(level === "All" ? "" : level)}
          >
            {level}
          </button>
        ))}
      </div>
    </fieldset>
  );
}
