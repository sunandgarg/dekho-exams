import { createFileRoute } from "@tanstack/react-router";
import { ArrowDown, ChevronRight } from "lucide-react";
import { ExamLogo } from "@/components/exams/exam-ui";
import { examBySlug } from "@/lib/question-bank";
import { pdfBrowsePath, pdfExams } from "@/lib/pdf-library";
import { seoHead } from "@/lib/seo";
export const Route = createFileRoute("/pdf-library/")({
  head: () =>
    seoHead({
      title: "Free previous year question papers and chapter-wise PDFs",
      description:
        "Download full exam papers by year and shift, or revise one chapter at a time across eight engineering entrance exams.",
      path: "pdf-library",
    }),
  component: () => (
    <div className="pdf-view">
      <header className="pdf-hero">
        <div className="pdf-container pdf-hero-grid">
          <div>
            <p className="pdf-kicker">Previous year question bank</p>
            <h1>
              Past papers. <br />
              <em>Ready to download.</em>
            </h1>
            <p>
              Practise a full exam or revise one chapter. Choose your paper and download the PDF for
              free.
            </p>
            <a className="pdf-download" href="#exams">
              Choose your exam <ArrowDown size={17} />
            </a>
          </div>
          <div className="pdf-cover" aria-hidden="true">
            <img src="/images/jee-paper-preview.jpg" width="410" height="580" alt="" />
          </div>
        </div>
      </header>
      <section className="pdf-container pdf-content" id="exams">
        <div className="pdf-group">
          <h2>Engineering entrance exams</h2>
          <span>{Object.keys(pdfExams).length} exams</span>
        </div>
        <div className="pdf-cards">
          {Object.entries(pdfExams).map(([slug, name]) => (
            <article key={slug}>
              <h3>
                <a href={"/pdf-library/" + slug}>
                  <ExamLogo exam={examBySlug(slug)!} />
                  {name}
                </a>
              </h3>
              <a href={pdfBrowsePath(slug, "paper")}>
                Question papers <ChevronRight size={16} />
              </a>
              <a href={pdfBrowsePath(slug, "chapter")}>
                Chapter wise <ChevronRight size={16} />
              </a>
            </article>
          ))}
        </div>
      </section>
    </div>
  ),
});
