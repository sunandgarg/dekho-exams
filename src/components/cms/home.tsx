import {
  ArrowRight,
  Award,
  BookOpen,
  CheckCheck,
  GraduationCap,
  Languages,
  School,
  Trophy,
  CalendarDays,
  FileCheck2,
  ClipboardList,
} from "lucide-react";
import { LANGUAGES } from "@/lib/education-catalog";
import { HOME_SHORTCUTS } from "@/lib/subject-directory";
import { GRADES } from "@/lib/school-content";
import { SubjectDirectory } from "@/components/subject-directory";
import languageArt from "@/data/language-art.json";

const shortcutIcons = {
  books: BookOpen,
  boards: School,
  exams: Trophy,
  practice: CheckCheck,
  awards: Award,
};

export function Home() {
  return (
    <div className="explore-home pen-home">
      <section className="pen-hero" aria-labelledby="home-heading">
        <div className="pen-hero-inner">
          <div className="pen-hero-intro">
            <h1 id="home-heading">Dekhoexams<span>.</span></h1>
            <p className="pen-hero-lead">What are you studying today?</p>
            <p className="pen-hero-copy">Find your class, open a chapter, or check an exam update.</p>
            <div className="pen-hero-actions">
              <a className="pen-hero-primary" href="/classes">Choose your class <ArrowRight aria-hidden="true" /></a>
              <a className="pen-hero-secondary" href="/ncert">Browse NCERT <ArrowRight aria-hidden="true" /></a>
            </div>
          </div>
        </div>
      </section>
      <section className="pen-exam-desk" aria-labelledby="exam-desk-heading">
        <div className="pen-exam-desk-inner">
          <div className="pen-exam-desk-intro">
            <h2 id="exam-desk-heading">Exam updates</h2>
            <p>Datesheets, answer keys and results from official sources.</p>
          </div>
          <nav className="pen-exam-desk-links" aria-label="Exam updates">
            <a href="/exam-updates/date-sheets"><CalendarDays aria-hidden="true" /> Date sheets <ArrowRight aria-hidden="true" /></a>
            <a href="/exam-updates/answer-keys"><FileCheck2 aria-hidden="true" /> Answer keys <ArrowRight aria-hidden="true" /></a>
            <a href="/exam-updates/results"><ClipboardList aria-hidden="true" /> Results <ArrowRight aria-hidden="true" /></a>
          </nav>
          <a className="pen-exam-desk-all" href="/exam-updates">All updates <ArrowRight aria-hidden="true" /></a>
        </div>
      </section>
      <div className="pen-home-content">
      <section className="pen-classes" aria-labelledby="classes-heading">
        <div className="pen-section-heading">
          <h2 id="classes-heading">Classes 1-12</h2>
          <a href="/classes">All classes <ArrowRight aria-hidden="true" /></a>
        </div>
        <div className="pen-class-grid">
          {GRADES.map((grade) => (
            <a href={`/class-${grade}`} key={grade}>
              <img className="pen-discovery-art" src={`/images/discovery/class-${grade}.png`} alt="" width={64} height={64} loading="lazy" decoding="async" />
              <span><strong>Class {grade}</strong><small>Lessons & practice</small></span>
              <ArrowRight aria-hidden="true" />
            </a>
          ))}
        </div>
      </section>
      <section aria-labelledby="collections-heading" className="pen-explore">
        <div className="pen-section-heading">
          <h2 id="collections-heading">Explore Dekhoexams</h2>
          <a href="/site-map">All collections <ArrowRight aria-hidden="true" /></a>
        </div>
        <div className="pen-shortcuts">
          {HOME_SHORTCUTS.map((item) => {
            const Icon = shortcutIcons[item.icon];
            return (
              <a
                key={item.path}
                href={item.path}
                className={`pen-shortcut pen-color-${item.color}`}
              >
                <div className="pen-shortcut-heading">
                  <h2>{item.title}</h2>
                  <Icon aria-hidden="true" />
                </div>
                <div className="pen-shortcut-detail">
                  <span>{item.detail}</span>
                  <ArrowRight aria-hidden="true" />
                </div>
              </a>
            );
          })}
        </div>
      </section>
      <SubjectDirectory />
      <section className="pen-languages" aria-labelledby="languages-heading">
        <div className="pen-section-heading">
          <h2 id="languages-heading">
            <Languages aria-hidden="true" /> NCERT by language
          </h2>
          <a href="/languages">
            All languages <ArrowRight aria-hidden="true" />
          </a>
        </div>
        <div className="pen-language-grid">
          {LANGUAGES.map(([slug, title, code]) => (
            <a href={`/ncert/${slug}`} key={slug}>
              <img
                className="pen-discovery-art"
                src={`/images/discovery/language-${slug}.png`}
                alt=""
                width={52}
                height={52}
                loading="lazy"
                decoding="async"
              />
              <span className="pen-language-name">
                <strong>{title}</strong>
                <small lang={code} dir={code === "ur" ? "rtl" : undefined}>
                  {languageArt[slug].native}
                </small>
              </span>
              <ArrowRight aria-hidden="true" />
            </a>
          ))}
        </div>
      </section>
      <section className="pen-continue">
        <GraduationCap aria-hidden="true" />
        <h2>Pick up where you left off</h2>
        <a href="/my-study">
          My Study <ArrowRight aria-hidden="true" />
        </a>
      </section>
      </div>
    </div>
  );
}
