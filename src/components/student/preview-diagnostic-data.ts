import { correct, performance, type Item } from "../../lib/mock-scoring.ts";

type Question = Item & { topic: string; chapter: string; next: string };

export const previewQuestions: Question[] = [
  {
    kind: "mcq",
    subject: "physics",
    topic: "Current electricity",
    chapter: "current-electricity",
    body: "A 3 Ω resistor and a 6 Ω resistor are connected in parallel across a 12 V battery. What total current does the battery supply?",
    options: ["2 A", "4 A", "6 A", "9 A"],
    choiceKey: 2,
    solution:
      "Each branch has 12 V across it. Ohm’s law gives 4 A through the 3 Ω resistor and 2 A through the 6 Ω resistor. The branch currents add to 6 A.",
    next: "Draw two parallel branches and use Ohm’s law on each one before adding the currents.",
  },
  {
    kind: "mcq",
    subject: "chemistry",
    topic: "Limiting reagents",
    chapter: "some-basic-concepts-of-chemistry",
    body: "Hydrogen reacts with oxygen according to 2H₂ + O₂ → 2H₂O. If 5 mol of H₂ and 2 mol of O₂ react until one reactant runs out, how many moles of water form?",
    options: ["2 mol", "4 mol", "5 mol", "7 mol"],
    choiceKey: 1,
    solution:
      "Two moles of O₂ react with 4 mol of H₂, so oxygen runs out first. The equation gives 2 mol of H₂O per mole of O₂, for 4 mol of water.",
    next: "For each reactant, divide its available moles by its coefficient. Start from the smallest value.",
  },
  {
    kind: "mcq",
    subject: "mathematics",
    topic: "Roots of quadratics",
    chapter: "quadratic-equation-and-inequalities",
    body: "The roots of x² − 7x + 12 = 0 are α and β. What is α² + β²?",
    options: ["13", "24", "25", "49"],
    choiceKey: 2,
    solution:
      "The sum of the roots is 7 and their product is 12. Then α² + β² = (α + β)² − 2αβ = 49 − 24 = 25.",
    next: "Write both the sum and product of the roots before simplifying expressions involving α and β.",
  },
  {
    kind: "mcq",
    subject: "physics",
    topic: "Work and kinetic energy",
    chapter: "work-power-and-energy",
    body: "A cart of mass 0.5 kg speeds up from 2 m/s to 6 m/s on a straight track. How much net work is done on it?",
    options: ["4 J", "8 J", "9 J", "16 J"],
    choiceKey: 1,
    solution:
      "Net work equals the change in kinetic energy. Using ½m(v² − u²) gives 0.25 × (36 − 4) J = 8 J.",
    next: "Calculate the initial and final kinetic energies separately. Squaring the change in speed gives a different result.",
  },
  {
    kind: "mcq",
    subject: "chemistry",
    topic: "Molecular shape",
    chapter: "chemical-bonding-and-molecular-structure",
    body: "The nitrogen atom in NH₃ has three N–H bonds and one lone pair. What is the molecular shape?",
    options: ["Bent", "Trigonal planar", "Trigonal pyramidal", "Tetrahedral"],
    choiceKey: 2,
    solution:
      "The four electron groups have a tetrahedral arrangement. The lone pair does not count as an atom in the molecular shape, leaving a trigonal pyramid.",
    next: "Draw the lone pairs and bonds, then name the shape formed by the bonded atoms.",
  },
  {
    kind: "mcq",
    subject: "mathematics",
    topic: "Arithmetic progressions",
    chapter: "sequences-and-series",
    body: "The second term of an arithmetic progression is 7 and its fifth term is 19. What is its tenth term?",
    options: ["27", "35", "39", "43"],
    choiceKey: 2,
    solution:
      "Three equal steps take the sequence from 7 to 19, so the common difference is 4. The tenth term is five steps after 19, giving 39.",
    next: "Use the difference in term numbers to find how many equal steps separate two known terms.",
  },
];

export const previewSubjects = ["physics", "chemistry", "mathematics"] as const;
export const blankPreviewAnswers = () => Array<string>(previewQuestions.length).fill("");

export function previewResult(answers: string[]) {
  const rows = previewQuestions.map((question, index) => {
    const answer = answers[index] ?? "";
    return {
      question,
      answer,
      index,
      outcome: !answer ? "Skipped" : correct(question, answer) ? "Correct" : "Incorrect",
    };
  });
  const subjects = previewSubjects.map((subject) => {
    const group = rows.filter(({ question }) => question.subject === subject);
    return {
      subject,
      ...performance(
        group.map(({ question }) => question),
        group.map(({ answer }) => answer),
      ),
    };
  });
  return {
    ...performance(previewQuestions, answers),
    rows,
    subjects,
    next:
      rows.find(({ outcome }) => outcome === "Incorrect") ??
      rows.find(({ outcome }) => outcome === "Skipped"),
  };
}
