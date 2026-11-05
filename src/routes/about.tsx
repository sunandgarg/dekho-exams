import { createFileRoute } from "@tanstack/react-router";
import { seoHead } from "@/lib/seo";

export const Route = createFileRoute("/about")({
  head: () => seoHead({
    title: "About Dekhoexams",
    description: "Dekhoexams is building free lessons and practice for students in Classes 1–12.",
    path: "about",
  }),
  component: AboutPage,
});

function AboutPage() {
  return (
    <div className="study-home study-lesson">
      <h1>About Dekhoexams</h1>
      <p className="study-intro">Dekhoexams is a new learning library for students in Classes 1–12.</p>
      <section>
        <h2>What is here today</h2>
        <p>Our first school lessons cover mathematics across Classes 1–12 and introductory science topics in Classes 6 and 10. Each lesson has a worked example and practice with explained answers. A separate computing library is also available.</p>
      </section>
      <section>
        <h2>How to use these resources</h2>
        <p>Use the lessons to understand and practise a concept. Check your current school syllabus and teacher guidance for exam requirements. Dekhoexams is independent and its lessons are not official board or textbook publications.</p>
      </section>
      <p><a href="/classes">Browse Classes 1–12 →</a></p>
    </div>
  );
}
