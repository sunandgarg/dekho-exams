import { useCallback, useEffect, useRef, useState } from "react";
import {
  Atom,
  BookOpen,
  Calculator,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Code2,
  GraduationCap,
  Landmark,
  Lightbulb,
  School,
} from "lucide-react";
import { SUBJECT_DIRECTORY, type DirectoryGroup } from "@/lib/subject-directory";

const icons = {
  maths: Calculator,
  science: Atom,
  english: BookOpen,
  computing: Code2,
  economics: Landmark,
  boards: School,
  explore: Lightbulb,
  teachers: GraduationCap,
};

export function SubjectDirectory() {
  const homeGroups = SUBJECT_DIRECTORY.filter(
    (group) => group.path !== "/explore-more" && group.path !== "/teachers",
  );
  const carouselRef = useRef<HTMLDivElement>(null);
  const [canScrollPrev, setCanScrollPrev] = useState(false);
  const [canScrollNext, setCanScrollNext] = useState(false);

  const updateControls = useCallback(() => {
    const viewport = carouselRef.current;
    if (!viewport) return;
    setCanScrollPrev(viewport.scrollLeft > 2);
    setCanScrollNext(viewport.scrollLeft + viewport.clientWidth < viewport.scrollWidth - 2);
  }, []);

  useEffect(() => {
    const viewport = carouselRef.current;
    if (!viewport) return;
    const observer = new ResizeObserver(updateControls);
    observer.observe(viewport);
    updateControls();
    return () => observer.disconnect();
  }, [updateControls]);

  const scrollSubjects = (direction: -1 | 1) => {
    const viewport = carouselRef.current;
    const slide = viewport?.querySelector<HTMLElement>(".subject-directory-slide");
    if (!viewport || !slide) return;
    const gap = parseFloat(getComputedStyle(slide.parentElement!).columnGap) || 0;
    viewport.scrollBy({ left: direction * (slide.offsetWidth + gap), behavior: "smooth" });
  };

  return (
    <section className="subject-directory" aria-labelledby="directory-title">
      <div className="pen-section-heading">
        <h2 id="directory-title">Find your next subject</h2>
        <div className="subject-directory-actions">
          <a href="/subjects">
            All subjects <span aria-hidden="true">→</span>
          </a>
          <div className="subject-directory-controls" aria-label="Subject carousel controls">
            <button type="button" aria-label="Previous subjects" title="Previous subjects" disabled={!canScrollPrev} onClick={() => scrollSubjects(-1)}>
              <ChevronLeft aria-hidden="true" />
            </button>
            <button type="button" aria-label="Next subjects" title="Next subjects" disabled={!canScrollNext} onClick={() => scrollSubjects(1)}>
              <ChevronRight aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>
      <div className="subject-directory-viewport" ref={carouselRef} onScroll={updateControls} role="region" aria-roledescription="carousel" aria-label="Subjects">
        <div className="subject-directory-track">
          {homeGroups.map((group, index) => (
            <div className="subject-directory-slide" key={group.id} role="group" aria-roledescription="slide" aria-label={`${index + 1} of ${homeGroups.length}: ${group.title}`}>
              <SubjectAccordion key={group.id} group={group} />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function SubjectAccordion({ group }: { group: DirectoryGroup }) {
  const [open, setOpen] = useState(false);
  const Icon = icons[group.icon];
  return (
    <div className="subject-accordion" data-open={open}>
      <h3>
        <button
          id={`trigger-${group.id}`}
          type="button"
          aria-expanded={open}
          aria-controls={`panel-${group.id}`}
          onClick={() => setOpen((value) => !value)}
        >
          <span className={`subject-symbol subject-symbol-${group.icon}`}>
            <Icon aria-hidden="true" strokeWidth={1.8} />
          </span>
          <span>{group.title}</span>
          <ChevronDown className="subject-chevron" aria-hidden="true" />
        </button>
      </h3>
      <div
        className="subject-panel"
        id={`panel-${group.id}`}
        role="region"
        aria-labelledby={`trigger-${group.id}`}
        aria-hidden={!open}
        inert={!open}
      >
        <div>
          <ul className="subject-options">
            {group.items.map((item, i) => (
              <li key={`${item.id}-${i}`}>
                <a href={item.href}>{item.label}</a>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
