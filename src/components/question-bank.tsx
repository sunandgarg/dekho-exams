import { useState } from "react";
import { useHydrated } from "@tanstack/react-router";
import { Bookmark, BookmarkCheck, Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { isCorrect, type Question } from "@/lib/question-bank";
import { useQuestionProgress } from "@/lib/question-progress";
import { toast } from "sonner";

export function PracticeNotice() {
  return (
    <p className="rounded-lg border bg-muted px-4 py-3 text-sm text-muted-foreground">
      These are original Dekhoexams practice questions in each exam's style. They are not past-paper
      questions, so they have no year or shift yet. Solutions have not been academically reviewed.
    </p>
  );
}

export function QuestionCard({ q, index }: { q: Question; index: number }) {
  const interactive = useHydrated();
  const p = useQuestionProgress();
  const prev = p.state.attempts[q.id];
  const [choice, setChoice] = useState<number | null>(null);
  const [text, setText] = useState("");
  const [checked, setChecked] = useState(false);
  const [showSol, setShowSol] = useState(false);
  const marked = p.state.bookmarks.includes(q.id);
  const response = q.type === "mcq" ? choice : text.trim() === "" ? null : Number(text);
  const ok = isCorrect(q, response);

  function check() {
    if (response === null || Number.isNaN(response)) {
      toast.error(q.type === "mcq" ? "Pick an option first." : "Enter a number first.");
      return;
    }
    setChecked(true);
    if (!p.record(q.id, response, ok)) toast.error("Your browser blocked saving progress.");
  }

  return (
    <article className="question-panel" data-subject={q.subject} aria-labelledby={`${q.id}-t`}>
      <div className="mb-3 flex flex-wrap items-center gap-2 text-xs">
        <span className="font-bold">Q{index + 1}</span>
        <Badge variant="secondary">{q.difficulty}</Badge>
        <Badge variant="outline">{q.type === "mcq" ? "Single correct" : "Numerical"}</Badge>
        {prev && <Badge variant={prev.ok ? "default" : "destructive"}>{prev.ok ? "Solved" : "Got wrong before"}</Badge>}
        <Button
          variant="ghost" size="sm" className="ml-auto"
          disabled={!interactive} aria-pressed={marked}
          onClick={() => { if (!p.toggleBookmark(q.id)) toast.error("Your browser blocked saving bookmarks."); }}
        >
          {marked ? <BookmarkCheck className="size-4" /> : <Bookmark className="size-4" />}
          {marked ? "Bookmarked" : "Bookmark"}
        </Button>
      </div>
      <p id={`${q.id}-t`} className="question-prompt mb-4">{q.text}</p>
      {q.type === "mcq" ? (
        <fieldset disabled={!interactive} className="grid min-w-0 gap-2" data-graded={checked || undefined}>
          <legend className="sr-only">Your answer for question {index + 1}</legend>
          {q.options!.map((o, i) => (
            <label key={i} className="answer-choice" data-correct={checked && i === q.answer || undefined}>
              <input type="radio" name={q.id} checked={choice === i}
                onChange={() => { setChoice(i); setChecked(false); }} />
              <b className="choice-letter">{String.fromCharCode(65 + i)}</b>
              <span>{o}</span>
            </label>
          ))}
        </fieldset>
      ) : (
        <Input disabled={!interactive} inputMode="decimal" aria-label="Your answer" placeholder="Type your numerical answer"
          value={text} onChange={(e) => { setText(e.target.value); setChecked(false); }} className="max-w-xs" />
      )}
      <div className="question-actions mt-4 flex flex-wrap items-center gap-3">
        <Button size="sm" disabled={!interactive} onClick={check}>Check answer</Button>
        <Button size="sm" disabled={!interactive} variant="outline" onClick={() => setShowSol(!showSol)} aria-expanded={showSol}>
          {showSol ? "Hide solution" : "Show solution"}
        </Button>
        {checked && (
          <span role="status" className={`flex items-center gap-1 text-sm font-bold ${ok ? "text-primary" : "text-destructive"}`}>
            {ok ? <Check className="size-4" /> : <X className="size-4" />}
            {ok ? "Correct" : q.type === "mcq" ? `Correct answer: ${String.fromCharCode(65 + q.answer)}` : "Not quite"}
          </span>
        )}
      </div>
      {showSol && (
        <div className="question-solution">
          <h3 className="mb-2 font-bold">Solution</h3>
          <p className="font-bold">Answer: {q.type === "mcq" ? `${String.fromCharCode(65 + q.answer)}. ${q.options![q.answer]}` : q.answer}</p>
          <p className="mt-1">{q.solution}</p>
        </div>
      )}
    </article>
  );
}
