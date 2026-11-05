import { createFileRoute, Link } from "@tanstack/react-router";
import { seoHead } from "@/lib/seo";
import { examBySlug, questionById } from "@/lib/question-bank";
import { QuestionCard } from "@/components/question-bank";
import { useQuestionProgress } from "@/lib/question-progress";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/questions/bookmarks")({
  head: () => seoHead({
    title: "Bookmarked Questions | Pencil2Pen",
    description: "Questions you bookmarked in the Pencil2Pen question bank, saved in this browser.",
    path: "questions/bookmarks",
    noindex: true,
  }),
  component: BookmarksPage,
});

function BookmarksPage() {
  const p = useQuestionProgress();
  const qs = p.state.bookmarks.map(questionById).filter((q) => !!q);
  return (
    <div className="study-home study-lesson">
      <p className="text-sm"><Link to="/questions">Question Bank</Link> / Bookmarks</p>
      <h1>Bookmarked questions</h1>
      <p className="study-intro">Bookmarks and progress are saved in this browser only. They don't sync across devices.</p>
      {qs.length === 0 ? <p>No bookmarks yet. Use the Bookmark button on any question.</p> : (
        <div className="grid gap-4">
          {qs.map((q, i) => (
            <div key={q.id}>
              <p className="mb-1 text-xs text-muted-foreground">{examBySlug(q.exam)?.name}</p>
              <QuestionCard q={q} index={i} />
            </div>
          ))}
        </div>
      )}
      <Button variant="outline" className="mt-8" onClick={() => { if (confirm("Clear all bookmarks and progress in this browser?")) p.reset(); }}>
        Reset bookmarks and progress
      </Button>
    </div>
  );
}
