import "./practice-medal.css";

export function PracticeMedal({ tier = "Gold" }: { tier?: string }) {
  return (
    <span className="practice-medal" data-tier={tier} aria-hidden="true">
      <span />
    </span>
  );
}
