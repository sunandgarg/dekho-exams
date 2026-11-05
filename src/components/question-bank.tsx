import { useState } from "react";
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
    <article className="rounded-xl border bg-card p-5 text-card-foreground" aria-labelledby={`${q.id}-t`}>
      <div className="mb-3 flex flex-wrap items-center gap-2 text-xs">
        <span className="font-bold">Q{index + 1}</span>
        <Badge variant="secondary">{q.difficulty}</Badge>
        <Badge variant="outline">{q.type === "mcq" ? "Single correct" : "Numerical"}</Badge>
        {prev && <Badge variant={prev.ok ? "default" : "destructive"}>{prev.ok ? "Solved" : "Got wrong before"}</Badge>}
        <Button
          variant="ghost" size="sm" className="ml-auto"
          aria-pressed={marked}
          onClick={() => { if (!p.toggleBookmark(q.id)) toast.error("Your browser blocked saving bookmarks."); }}
        >
          {marked ? <BookmarkCheck className="size-4" /> : <Bookmark className="size-4" />}
          {marked ? "Bookmarked" : "Bookmark"}
        </Button>
      </div>
      <p id={`${q.id}-t`} className="mb-4 font-medium leading-7">{q.text}</p>
      {q.type === "mcq" ? (
        <div className="grid gap-2" role="radiogroup">
          {q.options!.map((o, i) => {
            const state = checked && i === q.answer ? "border-primary bg-primary/10" : checked && i === choice ? "border-destructive bg-destructive/10" : choice === i ? "border-primary" : "";
            return (
              <button key={i} type="button" role="radio" aria-checked={choice === i}
                onClick={() => { setChoice(i); setChecked(false); }}
                className={`rounded-lg border px-4 py-2 text-left text-sm hover:bg-accent ${state}`}>
                <span className="mr-2 font-bold">{String.fromCharCode(65 + i)}.</span>{o}
              </button>
            );
          })}
        </div>
      ) : (
        <Input inputMode="decimal" aria-label="Your answer" placeholder="Type your numerical answer"
          value={text} onChange={(e) => { setText(e.target.value); setChecked(false); }} className="max-w-xs" />
      )}
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <Button size="sm" onClick={check}>Check answer</Button>
        <Button size="sm" variant="outline" onClick={() => setShowSol(!showSol)} aria-expanded={showSol}>
          {showSol ? "Hide solution" : "Show solution"}
        </Button>
        {checked && (
          <span className={`flex items-center gap-1 text-sm font-bold ${ok ? "text-primary" : "text-destructive"}`}>
            {ok ? <Check className="size-4" /> : <X className="size-4" />}
            {ok ? "Correct" : "Not quite"}
          </span>
        )}
      </div>
      {showSol && (
        <div className="mt-4 rounded-lg bg-muted p-4 text-sm leading-6">
          <p className="font-bold">Answer: {q.type === "mcq" ? `${String.fromCharCode(65 + q.answer)}. ${q.options![q.answer]}` : q.answer}</p>
          <p className="mt-1">{q.solution}</p>
        </div>
      )}
    </article>
  );
}
