import { useState } from "react";

const slides = [
  {
    title: "From source to execution",
    caption:
      "The compiler produces bytecode. The JVM loads classes and executes that bytecode; runtime compilation is a JVM implementation detail.",
    steps: [
      ["Source", ".java file", "Your declarations and expressions"],
      ["Compiler", "javac", "Type checks, then class files"],
      ["Runtime", "JVM", "Loads and executes bytecode"],
    ],
  },
  {
    title: "Choose a collection by its operations",
    caption:
      "These are operation families, not interchangeable storage choices. Match access patterns before comparing implementations.",
    steps: [
      ["List", "Position", "Ordered values, duplicates allowed"],
      ["Map", "Key", "One mapping per equal key"],
      ["Deque", "Endpoints", "Add and remove at either end"],
    ],
  },
  {
    title: "A reference is not an object copy",
    caption:
      "Two variables can contain references to the same object. Reassigning one variable does not change the other; mutating the shared object can affect both readers.",
    steps: [
      ["Caller", "Reference value", "Points to the shared list"],
      ["Method", "Copied reference", "Still points to that same list"],
      ["Object", "One mutable list", "Owns the actual element storage"],
    ],
  },
  {
    title: "Keep worker lifetime explicit",
    caption:
      "Submitting a task and waiting for its result are separate operations. Reject excess work deliberately and stop accepting work before waiting for shutdown.",
    steps: [
      ["Submit", "Admission policy", "Accept or reject the task"],
      ["Execute", "Worker thread", "Return a result or failure"],
      ["Close", "Shutdown policy", "Stop admission, then wait"],
    ],
  },
];

export function JavaConceptGallery() {
  const [index, setIndex] = useState(0);
  const slide = slides[index]!;
  return (
    <section
      aria-labelledby="java-diagrams"
      className="java-concept-gallery my-7 rounded-lg border"
    >
      <div className="p-4 sm:p-6">
        <h2 id="java-diagrams" className="font-display text-xl font-bold">
          Java, mapped out
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Original AI Trove diagrams · Java 8 foundations
        </p>
        <figure className="mt-5">
          <h3 className="mb-4 text-lg font-bold">{slide.title}</h3>
          <ol className="java-diagram-steps">
            {slide.steps.map(([label, value, explanation], step) => (
              <li key={label}>
                <span className="diagram-step-label">
                  {step + 1}. {label}
                </span>
                <strong>{value}</strong>
                <p>{explanation}</p>
                {step < 2 && (
                  <span className="diagram-connector" aria-hidden="true">
                    →
                  </span>
                )}
              </li>
            ))}
          </ol>
          <figcaption className="mt-4 text-sm leading-relaxed">{slide.caption}</figcaption>
        </figure>
      </div>
      <div className="diagram-controls flex items-center justify-between gap-3 border-t p-3">
        <button
          type="button"
          onClick={() => setIndex((value) => value - 1)}
          disabled={index === 0}
          aria-label="Previous Java diagram"
        >
          ← Previous
        </button>
        <span className="text-xs font-semibold" role="status">
          {index + 1} / {slides.length}
        </span>
        <button
          type="button"
          onClick={() => setIndex((value) => value + 1)}
          disabled={index === slides.length - 1}
          aria-label="Next Java diagram"
        >
          Next →
        </button>
      </div>
    </section>
  );
}
