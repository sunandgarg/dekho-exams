import { createFileRoute, Link } from "@tanstack/react-router";
import { seoHead } from "@/lib/seo";
import { EXAMS, questionsFor } from "@/lib/question-bank";
import { PracticeNotice } from "@/components/question-bank";
import { useQuestionProgress } from "@/lib/question-progress";

export const Route = createFileRoute("/questions/")({
  head: () => seoHead({
    title: "Question Bank — JEE, NEET, GATE & Board Practice | Dekhoexams",
    description: "Practise chapter-wise questions for JEE Main, JEE Advanced, NEET, GATE and school boards with solutions, bookmarks and timed practice.",
    path: "questions",
    noindex: true,
  }),
  component: QuestionsHome,
});

function QuestionsHome() {
  const p = useQuestionProgress();
  const categories = [...new Set(EXAMS.map((e) => e.category))];
  const attempted = Object.keys(p.state.attempts).length;
  const solved = Object.values(p.state.attempts).filter((a) => a.ok).length;
  return (
    <div className="study-home study-lesson">
      <h1>Question Bank</h1>
      <p className="study-intro">Pick an exam, then a subject and chapter. Practise one question at a time or run a timed set.</p>
      <PracticeNotice />
      <div className="my-6 flex flex-wrap gap-3 text-sm">
        <span className="rounded-lg border px-3 py-2">Attempted: <b>{attempted}</b></span>
        <span className="rounded-lg border px-3 py-2">Solved: <b>{solved}</b></span>
        <Link to="/questions/bookmarks" className="rounded-lg border px-3 py-2 font-bold">Bookmarks ({p.state.bookmarks.length}) →</Link>
      </div>
      {categories.map((c) => (
        <section key={c} className="mb-8">
          <h2>{c}</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {EXAMS.filter((e) => e.category === c).map((e) => {
              const n = questionsFor(e.slug).length;
              return (
                <Link key={e.slug} to="/questions/$exam" params={{ exam: e.slug }} className="rounded-xl border bg-card p-4 hover:bg-accent">
                  <span className="block font-bold">{e.name}</span>
                  <span className="text-sm text-muted-foreground">{e.subjects.length} subjects · {n} {n === 1 ? "question" : "questions"} so far</span>
                </Link>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
