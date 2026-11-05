// Dekhoexams question bank. Exam/subject/chapter structure follows the public
// syllabus layout of each exam. Every question here is an ORIGINAL practice
// question written for Dekhoexams — none are copied past-paper questions, so
// `year` and `shift` stay null until a verified, rights-cleared paper is added.

export type Difficulty = "easy" | "medium" | "hard";
export type Question = {
  id: string;
  version: number;
  exam: string;
  subject: string;
  chapter: string;
  type: "mcq" | "numeric";
  difficulty: Difficulty;
  text: string;
  options?: string[];
  answer: number; // option index for mcq, value for numeric
  tolerance?: number;
  solution: string;
  year: number | null;
  shift: string | null;
};
export type Marking = { correct: number; wrong: number; unattempted: number; numericWrong: number };
export type Subject = { slug: string; name: string; chapters: [slug: string, name: string][] };
export type Exam = { slug: string; name: string; category: string; marking: Marking; subjects: Subject[] };

const ch = (...names: string[]): [string, string][] =>
  names.map((n) => [n.toLowerCase().replace(/&/g, "and").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""), n]);

const PHY = ch("Units & Measurements", "Kinematics", "Laws of Motion", "Work Power & Energy", "Rotational Motion", "Gravitation", "Properties of Matter", "Thermodynamics", "Oscillations & Waves", "Electrostatics", "Current Electricity", "Magnetism", "Electromagnetic Induction", "Optics", "Modern Physics", "Semiconductors");
const CHE = ch("Mole Concept", "Atomic Structure", "Chemical Bonding", "States of Matter", "Chemical Equilibrium", "Thermochemistry", "Electrochemistry", "Chemical Kinetics", "Periodic Table", "Coordination Compounds", "Hydrocarbons", "Organic Reaction Mechanisms", "Biomolecules");
const MAT = ch("Sets & Relations", "Complex Numbers", "Quadratic Equations", "Sequences & Series", "Permutations & Combinations", "Binomial Theorem", "Matrices & Determinants", "Limits & Continuity", "Differentiation", "Integration", "Differential Equations", "Straight Lines", "Conic Sections", "Vectors & 3D Geometry", "Probability", "Statistics");
const BIO = ch("Cell Structure", "Cell Division", "Plant Physiology", "Human Physiology", "Genetics", "Molecular Basis of Inheritance", "Evolution", "Ecology", "Biotechnology", "Reproduction");
const ENG = (m: Marking) => (slug: string, name: string): Exam => ({
  slug, name, category: "Engineering entrance", marking: m,
  subjects: [{ slug: "physics", name: "Physics", chapters: PHY }, { slug: "chemistry", name: "Chemistry", chapters: CHE }, { slug: "mathematics", name: "Mathematics", chapters: MAT }],
});
const NEG = { correct: 4, wrong: -1, unattempted: 0, numericWrong: 0 };
const POS = { correct: 1, wrong: 0, unattempted: 0, numericWrong: 0 };
const gate = (slug: string, name: string, subjects: [string, string[]][]): Exam => ({
  slug, name, category: "GATE", marking: { correct: 2, wrong: -2 / 3, unattempted: 0, numericWrong: 0 },
  subjects: subjects.map(([n, c]) => ({ slug: ch(n)[0]![0], name: n, chapters: ch(...c) })),
});
const board = (slug: string, name: string, subjects: [string, string[]][]): Exam => ({
  slug, name, category: "School boards", marking: POS,
  subjects: subjects.map(([n, c]) => ({ slug: ch(n)[0]![0], name: n, chapters: ch(...c) })),
});

export const EXAMS: Exam[] = [
  ENG(NEG)("jee-main", "JEE Main"),
  ENG(NEG)("jee-advanced", "JEE Advanced"),
  ENG({ correct: 3, wrong: -1, unattempted: 0, numericWrong: 0 })("bitsat", "BITSAT"),
  ENG(POS)("wbjee", "WB JEE"),
  ENG(POS)("mht-cet", "MHT CET"),
  ENG(POS)("kcet", "KCET"),
  ENG(POS)("comedk", "COMEDK"),
  ENG(POS)("viteee", "VITEEE"),
  { slug: "neet", name: "NEET", category: "Medical entrance", marking: NEG, subjects: [{ slug: "physics", name: "Physics", chapters: PHY }, { slug: "chemistry", name: "Chemistry", chapters: CHE }, { slug: "biology", name: "Biology", chapters: BIO }] },
  gate("gate-cse", "GATE CSE", [["Data Structures", ["Arrays & Linked Lists", "Stacks & Queues", "Trees", "Graphs", "Hashing"]], ["Algorithms", ["Asymptotic Analysis", "Sorting & Searching", "Greedy", "Dynamic Programming"]], ["Digital Logic", ["Boolean Algebra", "Combinational Circuits", "Sequential Circuits", "Number Systems"]], ["Operating Systems", ["Processes & Threads", "CPU Scheduling", "Deadlocks", "Memory Management"]], ["DBMS", ["ER Model", "Relational Algebra", "SQL", "Normalization", "Transactions"]], ["Computer Networks", ["OSI & TCP/IP", "IP Addressing", "Routing", "Transport Layer"]], ["Theory of Computation", ["Regular Languages", "Context Free Languages", "Turing Machines"]]]),
  gate("gate-ece", "GATE ECE", [["Networks", ["Network Theorems", "Transient Analysis"]], ["Signals & Systems", ["LTI Systems", "Fourier Transform", "Z Transform"]], ["Analog Circuits", ["Diodes", "BJT & MOSFET", "Op-Amps"]], ["Communications", ["Analog Modulation", "Digital Communication"]]]),
  gate("gate-ee", "GATE EE", [["Electric Circuits", ["Network Theorems", "AC Circuits"]], ["Electrical Machines", ["Transformers", "Induction Machines", "DC Machines"]], ["Power Systems", ["Transmission Lines", "Fault Analysis"]], ["Control Systems", ["Transfer Functions", "Stability"]]]),
  gate("gate-me", "GATE ME", [["Engineering Mechanics", ["Statics", "Dynamics"]], ["Strength of Materials", ["Stress & Strain", "Bending", "Torsion"]], ["Thermodynamics", ["Laws of Thermodynamics", "Cycles"]], ["Fluid Mechanics", ["Fluid Statics", "Flow Through Pipes"]]]),
  gate("gate-ce", "GATE CE", [["Structural Analysis", ["Determinacy", "Influence Lines"]], ["Geotechnical Engineering", ["Soil Properties", "Consolidation"]], ["Environmental Engineering", ["Water Treatment", "Waste Water"]], ["Transportation", ["Highway Design", "Traffic Engineering"]]]),
  board("cbse-10", "CBSE Class 10", [["Mathematics", ["Real Numbers", "Polynomials", "Pair of Linear Equations", "Quadratic Equations", "Arithmetic Progressions", "Triangles", "Trigonometry", "Statistics", "Probability"]], ["Science", ["Chemical Reactions", "Acids Bases & Salts", "Life Processes", "Electricity", "Light"]]]),
  board("cbse-12", "CBSE Class 12", [["Physics", ["Electrostatics", "Current Electricity", "Magnetism", "Optics", "Modern Physics"]], ["Chemistry", ["Solutions", "Electrochemistry", "Chemical Kinetics", "Coordination Compounds"]], ["Mathematics", ["Relations & Functions", "Matrices", "Integration", "Probability"]]]),
  board("icse-10", "ICSE Class 10", [["Mathematics", ["Quadratic Equations", "Arithmetic Progression", "Trigonometry"]], ["Physics", ["Force", "Light", "Electricity"]]]),
  { slug: "nda", name: "NDA", category: "Defence", marking: { correct: 2.5, wrong: -0.83, unattempted: 0, numericWrong: 0 }, subjects: [{ slug: "mathematics", name: "Mathematics", chapters: MAT }, { slug: "general-ability", name: "General Ability", chapters: ch("English", "Physics", "Chemistry", "History", "Geography", "Current Events") }] },
];

type Q = Omit<Question, "version" | "year" | "shift" | "id"> & { id?: string };
const mcq = (exam: string, subject: string, chapter: string, difficulty: Difficulty, text: string, options: string[], answer: number, solution: string): Q =>
  ({ exam, subject, chapter, type: "mcq", difficulty, text, options, answer, solution });
const num = (exam: string, subject: string, chapter: string, difficulty: Difficulty, text: string, answer: number, solution: string): Q =>
  ({ exam, subject, chapter, type: "numeric", difficulty, text, answer, tolerance: 0.01, solution });

const RAW: Q[] = [
  mcq("jee-main", "physics", "kinematics", "easy", "A ball is thrown straight up at 20 m/s. Taking g = 10 m/s², what maximum height does it reach?", ["10 m", "20 m", "30 m", "40 m"], 1, "At the top v = 0, so h = u²/2g = 400/20 = 20 m."),
  num("jee-main", "physics", "kinematics", "easy", "A car starts from rest with a constant acceleration of 2 m/s². How far (in m) does it travel in 5 s?", 25, "s = ½at² = ½ × 2 × 25 = 25 m."),
  mcq("jee-main", "physics", "kinematics", "medium", "A projectile is launched at 45° with speed 20 m/s (g = 10 m/s²). Its horizontal range is:", ["20 m", "30 m", "40 m", "80 m"], 2, "R = u² sin 2θ / g = 400 × 1 / 10 = 40 m. At 45°, sin 2θ = 1, which also gives the maximum range."),
  mcq("jee-main", "physics", "laws-of-motion", "easy", "A 20 N horizontal force acts on a 5 kg block on a frictionless floor. Its acceleration is:", ["2 m/s²", "4 m/s²", "5 m/s²", "100 m/s²"], 1, "a = F/m = 20/5 = 4 m/s²."),
  num("jee-main", "physics", "laws-of-motion", "medium", "Blocks of 2 kg and 3 kg touch on a frictionless floor. A 10 N force pushes the 2 kg block. Find the contact force (in N) between them.", 6, "Common acceleration a = 10/5 = 2 m/s². The 3 kg block is moved only by the contact force: N = 3 × 2 = 6 N."),
  num("jee-main", "chemistry", "mole-concept", "easy", "How many moles are present in 36 g of water (H₂O, M = 18 g/mol)?", 2, "n = mass / molar mass = 36/18 = 2 mol."),
  mcq("jee-main", "chemistry", "mole-concept", "easy", "The volume occupied by 2 g of H₂ gas at STP (22.4 L/mol) is:", ["11.2 L", "22.4 L", "44.8 L", "2.24 L"], 1, "2 g of H₂ is 1 mol (M = 2 g/mol), which occupies 22.4 L at STP."),
  num("jee-main", "mathematics", "quadratic-equations", "medium", "If α and β are the roots of x² − 5x + 6 = 0, find α² + β².", 13, "α + β = 5, αβ = 6. α² + β² = (α + β)² − 2αβ = 25 − 12 = 13."),
  mcq("jee-main", "mathematics", "quadratic-equations", "easy", "For k > 0, x² + kx + 9 = 0 has equal roots when k equals:", ["3", "6", "9", "18"], 1, "Equal roots need discriminant 0: k² − 36 = 0, so k = 6."),
  num("jee-main", "mathematics", "sequences-and-series", "easy", "Find the sum of the first 20 natural numbers.", 210, "n(n + 1)/2 = 20 × 21 / 2 = 210."),
  mcq("jee-main", "mathematics", "sequences-and-series", "medium", "The 8th term of the GP 3, 6, 12, … is:", ["192", "384", "768", "96"], 1, "aₙ = a·rⁿ⁻¹ = 3 × 2⁷ = 384."),
  num("jee-advanced", "mathematics", "integration", "hard", "Evaluate ∫₀¹ x eˣ dx.", 1, "By parts: ∫x eˣ dx = x eˣ − eˣ. From 0 to 1: (e − e) − (0 − 1) = 1."),
  mcq("jee-advanced", "mathematics", "limits-and-continuity", "medium", "lim (x→0) (1 − cos x) / x² equals:", ["0", "1/2", "1", "2"], 1, "1 − cos x = 2 sin²(x/2). So the limit is 2 × (1/2)² × lim[sin(x/2)/(x/2)]² = 1/2."),
  mcq("neet", "biology", "cell-structure", "easy", "Which cell structure is the site of protein synthesis?", ["Lysosome", "Ribosome", "Golgi body", "Centriole"], 1, "Ribosomes translate mRNA into polypeptide chains. The Golgi body modifies and packages proteins but does not make them."),
  mcq("neet", "biology", "cell-division", "easy", "In which stage of mitosis do chromosomes line up at the cell's equator?", ["Prophase", "Metaphase", "Anaphase", "Telophase"], 1, "In metaphase, spindle fibres attach at the kinetochores and the chromosomes line up on the metaphase plate."),
  mcq("neet", "biology", "genetics", "easy", "In a monohybrid cross with complete dominance, the F₂ phenotypic ratio is:", ["1:2:1", "3:1", "9:3:3:1", "1:1"], 1, "Tt × Tt gives TT : Tt : tt = 1 : 2 : 1. TT and Tt look the same, so the phenotypes are 3 : 1."),
  num("neet", "biology", "genetics", "medium", "How many different genotypes appear in the F₂ of a dihybrid cross (AaBb × AaBb)?", 9, "Each gene gives 3 genotypes (AA, Aa, aa). Two independent genes give 3 × 3 = 9."),
  num("neet", "physics", "current-electricity", "easy", "Three 6 Ω resistors are connected in parallel. Find the equivalent resistance in Ω.", 2, "1/R = 1/6 + 1/6 + 1/6 = 1/2, so R = 2 Ω."),
  num("neet", "physics", "current-electricity", "medium", "A bulb is rated 100 W at 220 V. Find its resistance in Ω.", 484, "R = V²/P = 48400/100 = 484 Ω."),
  mcq("neet", "chemistry", "chemical-bonding", "easy", "The hybridisation of carbon in CH₄ is:", ["sp", "sp²", "sp³", "sp³d"], 2, "Carbon forms four σ bonds with no lone pair, so it uses four sp³ hybrid orbitals in a tetrahedral arrangement."),
  mcq("neet", "chemistry", "chemical-bonding", "medium", "The shape of the NH₃ molecule is:", ["Trigonal planar", "Tetrahedral", "Trigonal pyramidal", "Bent"], 2, "N has three bond pairs and one lone pair. The electron geometry is tetrahedral, but the molecular shape is trigonal pyramidal."),
  num("gate-cse", "data-structures", "trees", "easy", "What is the maximum number of nodes in a binary tree of height 3 (a single root node has height 0)?", 15, "Maximum nodes = 2^(h+1) − 1 = 2⁴ − 1 = 15."),
  mcq("gate-cse", "data-structures", "stacks-and-queues", "easy", "The postfix form of A + B * C is:", ["AB+C*", "ABC*+", "A+BC*", "ABC+*"], 1, "* has higher precedence, so B*C becomes BC*. Then A + (BC*) becomes ABC*+."),
  mcq("gate-cse", "algorithms", "sorting-and-searching", "easy", "The worst-case time complexity of quicksort with a fixed first-element pivot is:", ["O(n log n)", "O(n)", "O(n²)", "O(log n)"], 2, "On already-sorted input every partition is unbalanced (sizes n−1 and 0), so the total work is n + (n−1) + … = O(n²)."),
  num("gate-cse", "algorithms", "sorting-and-searching", "medium", "What is the maximum number of comparisons binary search makes on a sorted array of 1023 elements?", 10, "With n = 2^k − 1 elements, the worst case is k comparisons. 1023 = 2¹⁰ − 1, so the answer is 10."),
  num("gate-cse", "digital-logic", "combinational-circuits", "medium", "What is the minimum number of 2-input NAND gates needed to build a 2-input XOR?", 4, "Standard construction: N1 = NAND(A,B), N2 = NAND(A,N1), N3 = NAND(B,N1), XOR = NAND(N2,N3). That is 4 gates."),
  num("cbse-10", "mathematics", "real-numbers", "easy", "Find the HCF of 96 and 404.", 4, "96 = 2⁵ × 3 and 404 = 2² × 101. The common factor is 2² = 4."),
  num("cbse-10", "mathematics", "real-numbers", "easy", "Find the LCM of 12 and 18.", 36, "12 = 2² × 3 and 18 = 2 × 3². LCM = 2² × 3² = 36."),
  mcq("cbse-12", "physics", "electrostatics", "easy", "If the distance between two point charges is doubled, the force between them becomes:", ["F/2", "F/4", "2F", "4F"], 1, "Coulomb's law: F ∝ 1/r². Doubling r divides F by 4."),
];

export const QUESTIONS: Question[] = RAW.map((q, i) => ({
  ...q,
  id: q.id ?? `p2p-q${String(i + 1).padStart(4, "0")}`,
  version: 1,
  year: null,
  shift: null,
}));

export const examBySlug = (s: string) => EXAMS.find((e) => e.slug === s);
export const subjectOf = (e: Exam, s: string) => e.subjects.find((x) => x.slug === s);
export const chapterName = (sub: Subject, c: string) => sub.chapters.find(([slug]) => slug === c)?.[1];
export const questionsFor = (exam: string, subject?: string, chapter?: string) =>
  QUESTIONS.filter((q) => q.exam === exam && (!subject || q.subject === subject) && (!chapter || q.chapter === chapter));
export const questionById = (id: string) => QUESTIONS.find((q) => q.id === id);

export function isCorrect(q: Question, response: number | null | undefined): boolean {
  if (response === null || response === undefined || Number.isNaN(response)) return false;
  return q.type === "mcq" ? response === q.answer : Math.abs(response - q.answer) <= (q.tolerance ?? 0);
}

export function scoreAttempt(marking: Marking, questions: Question[], responses: Record<string, number | null>) {
  let score = 0, correct = 0, wrong = 0, unattempted = 0;
  for (const q of questions) {
    const r = responses[q.id];
    if (r === null || r === undefined || Number.isNaN(r)) { unattempted++; score += marking.unattempted; }
    else if (isCorrect(q, r)) { correct++; score += marking.correct; }
    else { wrong++; score += q.type === "numeric" ? marking.numericWrong : marking.wrong; }
  }
  return { score: Math.round(score * 100) / 100, max: questions.length * marking.correct, correct, wrong, unattempted };
}
