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
export type Unit = { name: string; chapters: [slug: string, name: string][] };
export type Subject = { slug: string; name: string; units: Unit[]; chapters: [slug: string, name: string][] };
export type Category = { slug: string; name: string; short: string };
export type Exam = { slug: string; name: string; short: string; category: string; marking: Marking; subjects: Subject[] };

const slugify = (n: string) => n.toLowerCase().replace(/&/g, "and").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const ch = (...names: string[]): [string, string][] => names.map((n) => [slugify(n), n]);
const subject = (name: string, units: [string, string[]][]): Subject => {
  const u = units.map(([n, c]) => ({ name: n, chapters: ch(...c) }));
  return { slug: slugify(name), name, units: u, chapters: u.flatMap((x) => x.chapters) };
};

export const CATEGORIES: Category[] = [
  { slug: "jee", name: "Joint Entrance Examination", short: "JEE" },
  { slug: "medical", name: "Medical", short: "Medical" },
  { slug: "gate", name: "Graduate Aptitude Test in Engineering", short: "GATE" },
  { slug: "civil-services", name: "Civil Services", short: "Civil Services" },
  { slug: "defence", name: "Defence", short: "Defence" },
  { slug: "ssc", name: "Staff Selection Commission", short: "SSC" },
  { slug: "cbse", name: "CBSE & School Boards", short: "CBSE" },
];

const PHYSICS = subject("Physics", [
  ["Mechanics", ["Units & Measurements", "Vector Algebra", "Motion in a Straight Line", "Motion in a Plane", "Circular Motion", "Laws of Motion", "Work Power & Energy", "Center of Mass and Collision", "Rotational Motion", "Mechanical Properties of Solids", "Mechanical Properties of Fluids", "Thermal Properties of Matter", "Thermodynamics", "Kinetic Theory of Gases", "Simple Harmonic Motion", "Waves", "Gravitation"]],
  ["Electricity", ["Electrostatics", "Current Electricity", "Capacitor", "Magnetic Effect of Current", "Magnetic Properties of Matter", "Electromagnetic Induction", "Alternating Current", "Electromagnetic Waves"]],
  ["Optics", ["Wave Optics", "Geometrical Optics"]],
  ["Modern Physics", ["Atoms and Nuclei", "Dual Nature of Radiation", "Semiconductor Devices"]],
]);
const CHEMISTRY = subject("Chemistry", [
  ["Physical Chemistry", ["Some Basic Concepts of Chemistry", "Structure of Atom", "States of Matter", "Thermodynamics", "Chemical Equilibrium", "Ionic Equilibrium", "Redox Reactions", "Solutions", "Electrochemistry", "Chemical Kinetics", "Surface Chemistry"]],
  ["Inorganic Chemistry", ["Periodic Table & Periodicity", "Chemical Bonding & Molecular Structure", "Hydrogen", "s-Block Elements", "p-Block Elements", "d and f Block Elements", "Coordination Compounds", "Salt Analysis"]],
  ["Organic Chemistry", ["Basics of Organic Chemistry", "Hydrocarbons", "Haloalkanes and Haloarenes", "Alcohols Phenols and Ethers", "Aldehydes Ketones and Carboxylic Acids", "Compounds Containing Nitrogen", "Biomolecules", "Polymers"]],
]);
const MATHEMATICS = subject("Mathematics", [
  ["Algebra", ["Sets and Relations", "Logarithm", "Quadratic Equation and Inequalities", "Sequences and Series", "Mathematical Induction", "Binomial Theorem", "Matrices and Determinants", "Permutations and Combinations", "Probability", "Vector Algebra", "3D Geometry", "Statistics", "Complex Numbers"]],
  ["Trigonometry", ["Trigonometric Ratio & Identities", "Trigonometric Equations", "Inverse Trigonometric Functions", "Properties of Triangle", "Height and Distance"]],
  ["Coordinate Geometry", ["Straight Lines and Pair of Straight Lines", "Circle", "Parabola", "Ellipse", "Hyperbola"]],
  ["Calculus", ["Functions", "Limits Continuity and Differentiability", "Differentiation", "Application of Derivatives", "Indefinite Integrals", "Definite Integration", "Application of Integration", "Differential Equations"]],
]);
const BIOLOGY = subject("Biology", [
  ["Botany", ["Cell Structure", "Cell Division", "Plant Physiology", "Plant Reproduction", "Genetics", "Molecular Basis of Inheritance", "Ecology"]],
  ["Zoology", ["Human Physiology", "Human Reproduction", "Evolution", "Biotechnology", "Human Health and Disease"]],
]);
const PCM = [PHYSICS, CHEMISTRY, MATHEMATICS];
const PCB = [PHYSICS, CHEMISTRY, BIOLOGY];
const NEG = { correct: 4, wrong: -1, unattempted: 0, numericWrong: 0 };
const POS = { correct: 1, wrong: 0, unattempted: 0, numericWrong: 0 };
const GATE_M = { correct: 2, wrong: -2 / 3, unattempted: 0, numericWrong: 0 };
const flat = (name: string, chapters: string[]) => subject(name, [[name, chapters]]);
const exam = (category: string, slug: string, name: string, short: string, marking: Marking, subjects: Subject[]): Exam =>
  ({ slug, name, short, category, marking, subjects });
const GATE_APT = flat("General Aptitude", ["Verbal Aptitude", "Quantitative Aptitude", "Analytical Aptitude", "Spatial Aptitude"]);
const ENG_MATH = flat("Engineering Mathematics", ["Linear Algebra", "Calculus", "Differential Equations", "Probability and Statistics", "Numerical Methods"]);

export const EXAMS: Exam[] = [
  exam("jee", "jee-main", "JEE Main", "JM", NEG, PCM),
  exam("jee", "jee-advanced", "JEE Advanced", "JA", NEG, PCM),
  exam("jee", "mht-cet", "MHT CET", "MC", POS, PCM),
  exam("jee", "bitsat", "BITSAT", "BI", { correct: 3, wrong: -1, unattempted: 0, numericWrong: 0 }, PCM),
  exam("jee", "comedk", "COMEDK", "CK", POS, PCM),
  exam("jee", "wbjee", "WB JEE", "WB", POS, PCM),
  exam("jee", "kcet", "KCET", "KC", POS, PCM),
  exam("jee", "viteee", "VITEEE", "VI", POS, PCM),
  exam("jee", "ap-eapcet", "AP EAPCET", "AP", POS, PCM),
  exam("jee", "ts-eamcet", "TS EAMCET", "TS", POS, PCM),
  exam("jee", "iat", "IAT (IISER)", "IA", NEG, [...PCM, BIOLOGY]),
  exam("medical", "neet", "NEET", "NE", NEG, PCB),
  exam("medical", "mht-cet-pcb", "MHT CET (PCB)", "MC", POS, PCB),
  exam("medical", "aiims", "AIIMS", "AI", NEG, PCB),
  exam("medical", "jipmer", "JIPMER", "JP", NEG, PCB),
  exam("gate", "gate-cse", "GATE CSE", "CS", GATE_M, [
    subject("Data Structures", [["Data Structures", ["Arrays & Linked Lists", "Stacks & Queues", "Trees", "Graphs", "Hashing"]]]),
    flat("Algorithms", ["Asymptotic Analysis", "Sorting & Searching", "Greedy", "Dynamic Programming"]),
    flat("Digital Logic", ["Boolean Algebra", "Combinational Circuits", "Sequential Circuits", "Number Systems"]),
    flat("Operating Systems", ["Processes & Threads", "CPU Scheduling", "Deadlocks", "Memory Management"]),
    flat("DBMS", ["ER Model", "Relational Algebra", "SQL", "Normalization", "Transactions"]),
    flat("Computer Networks", ["OSI & TCP/IP", "IP Addressing", "Routing", "Transport Layer"]),
    flat("Theory of Computation", ["Regular Languages", "Context Free Languages", "Turing Machines"]),
    ENG_MATH, GATE_APT,
  ]),
  exam("gate", "gate-ece", "GATE ECE", "EC", GATE_M, [flat("Networks", ["Network Theorems", "Transient Analysis"]), flat("Signals & Systems", ["LTI Systems", "Fourier Transform", "Z Transform"]), flat("Analog Circuits", ["Diodes", "BJT & MOSFET", "Op-Amps"]), flat("Communications", ["Analog Modulation", "Digital Communication"]), ENG_MATH, GATE_APT]),
  exam("gate", "gate-ee", "GATE EE", "EE", GATE_M, [flat("Electric Circuits", ["Network Theorems", "AC Circuits"]), flat("Electrical Machines", ["Transformers", "Induction Machines", "DC Machines"]), flat("Power Systems", ["Transmission Lines", "Fault Analysis"]), flat("Control Systems", ["Transfer Functions", "Stability"]), ENG_MATH, GATE_APT]),
  exam("gate", "gate-me", "GATE ME", "ME", GATE_M, [flat("Engineering Mechanics", ["Statics", "Dynamics"]), flat("Strength of Materials", ["Stress & Strain", "Bending", "Torsion"]), flat("Thermodynamics", ["Laws of Thermodynamics", "Cycles"]), flat("Fluid Mechanics", ["Fluid Statics", "Flow Through Pipes"]), ENG_MATH, GATE_APT]),
  exam("gate", "gate-ce", "GATE CE", "CE", GATE_M, [flat("Structural Analysis", ["Determinacy", "Influence Lines"]), flat("Geotechnical Engineering", ["Soil Properties", "Consolidation"]), flat("Environmental Engineering", ["Water Treatment", "Waste Water"]), flat("Transportation", ["Highway Design", "Traffic Engineering"]), ENG_MATH, GATE_APT]),
  exam("gate", "gate-pi", "GATE PI", "PI", GATE_M, [flat("Manufacturing", ["Casting", "Machining", "Welding", "Metrology"]), flat("Industrial Engineering", ["Operations Research", "Production Planning", "Quality Control"]), ENG_MATH, GATE_APT]),
  exam("gate", "gate-in", "GATE IN", "IN", GATE_M, [flat("Measurements", ["Sensors and Transducers", "Electrical Measurements"]), flat("Control Systems", ["Transfer Functions", "Stability"]), flat("Analog Electronics", ["Op-Amps", "Filters"]), ENG_MATH, GATE_APT]),
  exam("gate", "gate-da", "GATE Data Science and AI", "DA", GATE_M, [flat("Machine Learning", ["Regression", "Classification", "Clustering", "Neural Networks"]), flat("Programming & DSA", ["Python Programming", "Data Structures", "Algorithms"]), flat("Database & Warehousing", ["Relational Model", "SQL", "Data Warehousing"]), ENG_MATH, GATE_APT]),
  exam("civil-services", "upsc-prelims", "UPSC Civil Services Prelims", "UP", { correct: 2, wrong: -0.66, unattempted: 0, numericWrong: 0 }, [
    flat("General Studies", ["History", "Geography", "Indian Polity", "Indian Economy", "Environment & Ecology", "Science & Technology", "Current Affairs"]),
    flat("CSAT", ["Comprehension", "Logical Reasoning", "Basic Numeracy", "Data Interpretation"]),
  ]),
  exam("defence", "nda", "NDA", "ND", { correct: 2.5, wrong: -0.83, unattempted: 0, numericWrong: 0 }, [MATHEMATICS, flat("General Ability", ["English", "Physics", "Chemistry", "History", "Geography", "Current Events"])]),
  exam("ssc", "ssc-cgl", "SSC CGL", "SG", { correct: 2, wrong: -0.5, unattempted: 0, numericWrong: 0 }, [
    flat("Quantitative Aptitude", ["Number System", "Percentage", "Profit and Loss", "Time and Work", "Geometry", "Trigonometry"]),
    flat("General Intelligence & Reasoning", ["Analogy", "Series", "Coding Decoding", "Blood Relations"]),
    flat("English Comprehension", ["Grammar", "Vocabulary", "Reading Comprehension"]),
    flat("General Awareness", ["History", "Geography", "Polity", "Economics", "General Science"]),
  ]),
  exam("cbse", "cbse-12", "CBSE Class 12", "12", POS, [flat("Physics", ["Electrostatics", "Current Electricity", "Magnetism", "Optics", "Modern Physics"]), flat("Chemistry", ["Solutions", "Electrochemistry", "Chemical Kinetics", "Coordination Compounds"]), flat("Mathematics", ["Relations & Functions", "Matrices", "Integration", "Probability"])]),
  exam("cbse", "cbse-10", "CBSE Class 10", "10", POS, [flat("Mathematics", ["Real Numbers", "Polynomials", "Pair of Linear Equations", "Quadratic Equations", "Arithmetic Progressions", "Triangles", "Trigonometry", "Statistics", "Probability"]), flat("Science", ["Chemical Reactions", "Acids Bases & Salts", "Life Processes", "Electricity", "Light"])]),
  exam("cbse", "icse-10", "ICSE Class 10", "IC", POS, [flat("Mathematics", ["Quadratic Equations", "Arithmetic Progression", "Trigonometry"]), flat("Physics", ["Force", "Light", "Electricity"])]),
];

type Q = Omit<Question, "version" | "year" | "shift" | "id"> & { id?: string };
const mcq = (exam: string, subject: string, chapter: string, difficulty: Difficulty, text: string, options: string[], answer: number, solution: string): Q =>
  ({ exam, subject, chapter, type: "mcq", difficulty, text, options, answer, solution });
const num = (exam: string, subject: string, chapter: string, difficulty: Difficulty, text: string, answer: number, solution: string): Q =>
  ({ exam, subject, chapter, type: "numeric", difficulty, text, answer, tolerance: 0.01, solution });

const RAW: Q[] = [
  mcq("jee-main", "physics", "motion-in-a-straight-line", "easy", "A ball is thrown straight up at 20 m/s. Taking g = 10 m/s², what maximum height does it reach?", ["10 m", "20 m", "30 m", "40 m"], 1, "At the top v = 0, so h = u²/2g = 400/20 = 20 m."),
  num("jee-main", "physics", "motion-in-a-straight-line", "easy", "A car starts from rest with a constant acceleration of 2 m/s². How far (in m) does it travel in 5 s?", 25, "s = ½at² = ½ × 2 × 25 = 25 m."),
  mcq("jee-main", "physics", "motion-in-a-plane", "medium", "A projectile is launched at 45° with speed 20 m/s (g = 10 m/s²). Its horizontal range is:", ["20 m", "30 m", "40 m", "80 m"], 2, "R = u² sin 2θ / g = 400 × 1 / 10 = 40 m. At 45°, sin 2θ = 1, which also gives the maximum range."),
  mcq("jee-main", "physics", "laws-of-motion", "easy", "A 20 N horizontal force acts on a 5 kg block on a frictionless floor. Its acceleration is:", ["2 m/s²", "4 m/s²", "5 m/s²", "100 m/s²"], 1, "a = F/m = 20/5 = 4 m/s²."),
  num("jee-main", "physics", "laws-of-motion", "medium", "Blocks of 2 kg and 3 kg touch on a frictionless floor. A 10 N force pushes the 2 kg block. Find the contact force (in N) between them.", 6, "Common acceleration a = 10/5 = 2 m/s². The 3 kg block is moved only by the contact force: N = 3 × 2 = 6 N."),
  num("jee-main", "chemistry", "some-basic-concepts-of-chemistry", "easy", "How many moles are present in 36 g of water (H₂O, M = 18 g/mol)?", 2, "n = mass / molar mass = 36/18 = 2 mol."),
  mcq("jee-main", "chemistry", "some-basic-concepts-of-chemistry", "easy", "The volume occupied by 2 g of H₂ gas at STP (22.4 L/mol) is:", ["11.2 L", "22.4 L", "44.8 L", "2.24 L"], 1, "2 g of H₂ is 1 mol (M = 2 g/mol), which occupies 22.4 L at STP."),
  num("jee-main", "mathematics", "quadratic-equation-and-inequalities", "medium", "If α and β are the roots of x² − 5x + 6 = 0, find α² + β².", 13, "α + β = 5, αβ = 6. α² + β² = (α + β)² − 2αβ = 25 − 12 = 13."),
  mcq("jee-main", "mathematics", "quadratic-equation-and-inequalities", "easy", "For k > 0, x² + kx + 9 = 0 has equal roots when k equals:", ["3", "6", "9", "18"], 1, "Equal roots need discriminant 0: k² − 36 = 0, so k = 6."),
  num("jee-main", "mathematics", "sequences-and-series", "easy", "Find the sum of the first 20 natural numbers.", 210, "n(n + 1)/2 = 20 × 21 / 2 = 210."),
  mcq("jee-main", "mathematics", "sequences-and-series", "medium", "The 8th term of the GP 3, 6, 12, … is:", ["192", "384", "768", "96"], 1, "aₙ = a·rⁿ⁻¹ = 3 × 2⁷ = 384."),
  num("jee-advanced", "mathematics", "definite-integration", "hard", "Evaluate ∫₀¹ x eˣ dx.", 1, "By parts: ∫x eˣ dx = x eˣ − eˣ. From 0 to 1: (e − e) − (0 − 1) = 1."),
  mcq("jee-advanced", "mathematics", "limits-continuity-and-differentiability", "medium", "lim (x→0) (1 − cos x) / x² equals:", ["0", "1/2", "1", "2"], 1, "1 − cos x = 2 sin²(x/2). So the limit is 2 × (1/2)² × lim[sin(x/2)/(x/2)]² = 1/2."),
  mcq("neet", "biology", "cell-structure", "easy", "Which cell structure is the site of protein synthesis?", ["Lysosome", "Ribosome", "Golgi body", "Centriole"], 1, "Ribosomes translate mRNA into polypeptide chains. The Golgi body modifies and packages proteins but does not make them."),
  mcq("neet", "biology", "cell-division", "easy", "In which stage of mitosis do chromosomes line up at the cell's equator?", ["Prophase", "Metaphase", "Anaphase", "Telophase"], 1, "In metaphase, spindle fibres attach at the kinetochores and the chromosomes line up on the metaphase plate."),
  mcq("neet", "biology", "genetics", "easy", "In a monohybrid cross with complete dominance, the F₂ phenotypic ratio is:", ["1:2:1", "3:1", "9:3:3:1", "1:1"], 1, "Tt × Tt gives TT : Tt : tt = 1 : 2 : 1. TT and Tt look the same, so the phenotypes are 3 : 1."),
  num("neet", "biology", "genetics", "medium", "How many different genotypes appear in the F₂ of a dihybrid cross (AaBb × AaBb)?", 9, "Each gene gives 3 genotypes (AA, Aa, aa). Two independent genes give 3 × 3 = 9."),
  num("neet", "physics", "current-electricity", "easy", "Three 6 Ω resistors are connected in parallel. Find the equivalent resistance in Ω.", 2, "1/R = 1/6 + 1/6 + 1/6 = 1/2, so R = 2 Ω."),
  num("neet", "physics", "current-electricity", "medium", "A bulb is rated 100 W at 220 V. Find its resistance in Ω.", 484, "R = V²/P = 48400/100 = 484 Ω."),
  mcq("neet", "chemistry", "chemical-bonding-and-molecular-structure", "easy", "The hybridisation of carbon in CH₄ is:", ["sp", "sp²", "sp³", "sp³d"], 2, "Carbon forms four σ bonds with no lone pair, so it uses four sp³ hybrid orbitals in a tetrahedral arrangement."),
  mcq("neet", "chemistry", "chemical-bonding-and-molecular-structure", "medium", "The shape of the NH₃ molecule is:", ["Trigonal planar", "Tetrahedral", "Trigonal pyramidal", "Bent"], 2, "N has three bond pairs and one lone pair. The electron geometry is tetrahedral, but the molecular shape is trigonal pyramidal."),
  num("gate-cse", "data-structures", "trees", "easy", "What is the maximum number of nodes in a binary tree of height 3 (a single root node has height 0)?", 15, "Maximum nodes = 2^(h+1) − 1 = 2⁴ − 1 = 15."),
  mcq("gate-cse", "data-structures", "stacks-and-queues", "easy", "The postfix form of A + B * C is:", ["AB+C*", "ABC*+", "A+BC*", "ABC+*"], 1, "* has higher precedence, so B*C becomes BC*. Then A + (BC*) becomes ABC*+."),
  mcq("gate-cse", "algorithms", "sorting-and-searching", "easy", "The worst-case time complexity of quicksort with a fixed first-element pivot is:", ["O(n log n)", "O(n)", "O(n²)", "O(log n)"], 2, "On already-sorted input every partition is unbalanced (sizes n−1 and 0), so the total work is n + (n−1) + … = O(n²)."),
  num("gate-cse", "algorithms", "sorting-and-searching", "medium", "What is the maximum number of comparisons binary search makes on a sorted array of 1023 elements?", 10, "With n = 2^k − 1 elements, the worst case is k comparisons. 1023 = 2¹⁰ − 1, so the answer is 10."),
  num("gate-cse", "digital-logic", "combinational-circuits", "medium", "What is the minimum number of 2-input NAND gates needed to build a 2-input XOR?", 4, "Standard construction: N1 = NAND(A,B), N2 = NAND(A,N1), N3 = NAND(B,N1), XOR = NAND(N2,N3). That is 4 gates."),
  num("cbse-10", "mathematics", "real-numbers", "easy", "Find the HCF of 96 and 404.", 4, "96 = 2⁵ × 3 and 404 = 2² × 101. The common factor is 2² = 4."),
  num("cbse-10", "mathematics", "real-numbers", "easy", "Find the LCM of 12 and 18.", 36, "12 = 2² × 3 and 18 = 2 × 3². LCM = 2² × 3² = 36."),
  mcq("cbse-12", "physics", "electrostatics", "easy", "If the distance between two point charges is doubled, the force between them becomes:", ["F/2", "F/4", "2F", "4F"], 1, "Coulomb's law: F ∝ 1/r². Doubling r divides F by 4."),
  // Batch 2 (2026-11-05): appended only, so earlier IDs stay stable.
  mcq("jee-main", "physics", "units-and-measurements", "easy", "The dimensional formula of force is:", ["[MLT⁻¹]", "[MLT⁻²]", "[ML²T⁻²]", "[M⁰LT⁻²]"], 1, "F = ma, so [F] = [M][LT⁻²] = [MLT⁻²]."),
  num("jee-main", "physics", "work-power-and-energy", "easy", "A 2 kg body moves at 3 m/s. Find its kinetic energy in J.", 9, "KE = ½mv² = ½ × 2 × 9 = 9 J."),
  num("jee-main", "physics", "gravitation", "medium", "If Earth's radius shrank to half with mass unchanged, by what factor would g at the surface increase?", 4, "g = GM/R². Halving R multiplies g by 1/(1/2)² = 4."),
  mcq("jee-main", "physics", "simple-harmonic-motion", "medium", "The period of a simple pendulum of length 1 m is T. If the length becomes 4 m, the period becomes:", ["T", "2T", "4T", "T/2"], 1, "T ∝ √L. Four times the length gives √4 = 2 times the period."),
  num("jee-main", "physics", "current-electricity", "easy", "A 12 V battery drives 3 A through a resistor. Find the resistance in Ω.", 4, "R = V/I = 12/3 = 4 Ω."),
  mcq("jee-main", "physics", "geometrical-optics", "easy", "A concave mirror has focal length 10 cm. Its radius of curvature is:", ["5 cm", "10 cm", "20 cm", "40 cm"], 2, "For a spherical mirror R = 2f = 20 cm."),
  num("jee-main", "physics", "dual-nature-of-radiation", "medium", "Light of energy 5 eV falls on a metal with work function 3 eV. Find the maximum kinetic energy of emitted electrons in eV.", 2, "Einstein's equation: KEmax = hν − φ = 5 − 3 = 2 eV."),
  num("jee-main", "chemistry", "structure-of-atom", "easy", "How many electrons can occupy a single orbital?", 2, "Pauli's exclusion principle allows at most two electrons, with opposite spins, in one orbital."),
  mcq("jee-main", "chemistry", "ionic-equilibrium", "easy", "The pH of a 0.01 M HCl solution is:", ["1", "2", "12", "7"], 1, "HCl is a strong acid, so [H⁺] = 10⁻² M and pH = −log 10⁻² = 2."),
  mcq("jee-main", "chemistry", "periodic-table-and-periodicity", "easy", "Which element has the highest electronegativity?", ["Oxygen", "Chlorine", "Fluorine", "Nitrogen"], 2, "Fluorine has the highest Pauling electronegativity (about 4.0)."),
  mcq("jee-main", "chemistry", "hydrocarbons", "easy", "The general formula of alkenes is:", ["CₙH₂ₙ₊₂", "CₙH₂ₙ", "CₙH₂ₙ₋₂", "CₙHₙ"], 1, "One C=C double bond removes two hydrogens from the alkane formula CₙH₂ₙ₊₂, giving CₙH₂ₙ."),
  num("jee-main", "chemistry", "chemical-kinetics", "medium", "A first-order reaction has a half-life of 10 min. What percentage of the reactant remains after 30 min?", 12.5, "30 min is three half-lives: 100 → 50 → 25 → 12.5%."),
  mcq("jee-main", "mathematics", "complex-numbers", "easy", "The value of i⁴⁵ is:", ["1", "−1", "i", "−i"], 2, "45 = 4 × 11 + 1, so i⁴⁵ = i¹ = i."),
  num("jee-main", "mathematics", "permutations-and-combinations", "easy", "In how many ways can 5 different books be arranged on a shelf?", 120, "5! = 120."),
  num("jee-main", "mathematics", "binomial-theorem", "medium", "Find the coefficient of x² in (1 + x)⁵.", 10, "The coefficient is ⁵C₂ = 10."),
  num("jee-main", "mathematics", "matrices-and-determinants", "easy", "Find the determinant of the matrix [[2, 3], [1, 4]].", 5, "2 × 4 − 3 × 1 = 5."),
  mcq("jee-main", "mathematics", "differentiation", "easy", "d/dx (sin x · x) equals:", ["cos x", "x cos x", "sin x + x cos x", "sin x − x cos x"], 2, "Product rule: (sin x)′x + sin x(x)′ = x cos x + sin x."),
  num("jee-main", "mathematics", "circle", "easy", "Find the radius of the circle x² + y² − 6x − 8y = 0.", 5, "Centre (3, 4); r = √(9 + 16 − 0) = 5."),
  num("jee-main", "mathematics", "probability", "easy", "Two fair coins are tossed. The probability of getting exactly one head is p. Find 4p.", 2, "Outcomes HT and TH out of 4, so p = 1/2 and 4p = 2."),
  num("jee-advanced", "physics", "rotational-motion", "hard", "A solid sphere rolls without slipping. What percentage of its total kinetic energy is rotational? (Give the nearest whole number.)", 29, "KE_rot = ½·(2/5)mR²ω² = (1/5)mv²; KE_total = (7/10)mv². Ratio = 2/7 ≈ 28.6%, nearest 29."),
  mcq("jee-advanced", "chemistry", "coordination-compounds", "medium", "The coordination number of Fe in [Fe(CN)₆]³⁻ is:", ["3", "4", "6", "9"], 2, "Six monodentate cyanide ligands bind Fe, so the coordination number is 6."),
  mcq("bitsat", "physics", "electrostatics", "easy", "The SI unit of electric field is:", ["N/C", "C/N", "J/C²", "N·C"], 0, "E = F/q, so its unit is newton per coulomb."),
  num("bitsat", "mathematics", "sequences-and-series", "easy", "Find the 10th term of the AP 2, 5, 8, …", 29, "aₙ = a + (n − 1)d = 2 + 9 × 3 = 29."),
  mcq("mht-cet", "chemistry", "solutions", "easy", "Molarity is defined as moles of solute per:", ["kg of solvent", "litre of solution", "litre of solvent", "kg of solution"], 1, "Molarity M = moles of solute / volume of solution in litres."),
  num("mht-cet", "mathematics", "definite-integration", "easy", "Evaluate ∫₀² 3x² dx.", 8, "∫3x² dx = x³; from 0 to 2 gives 8."),
  mcq("wbjee", "physics", "waves", "easy", "Sound waves in air are:", ["Transverse", "Longitudinal", "Electromagnetic", "Stationary only"], 1, "Air particles vibrate along the direction of travel, so sound in air is longitudinal."),
  mcq("kcet", "chemistry", "s-block-elements", "easy", "Which of these is an alkali metal?", ["Calcium", "Magnesium", "Sodium", "Aluminium"], 2, "Sodium is in Group 1; calcium and magnesium are Group 2."),
  num("comedk", "mathematics", "straight-lines-and-pair-of-straight-lines", "easy", "Find the slope of the line 2x − y + 5 = 0.", 2, "y = 2x + 5, so the slope is 2."),
  mcq("viteee", "physics", "semiconductor-devices", "easy", "In an n-type semiconductor the majority charge carriers are:", ["Holes", "Electrons", "Protons", "Ions"], 1, "Pentavalent dopants donate extra electrons, making electrons the majority carriers."),
  num("ap-eapcet", "mathematics", "quadratic-equation-and-inequalities", "easy", "Find the product of the roots of 2x² − 7x + 6 = 0.", 3, "Product = c/a = 6/2 = 3."),
  mcq("ts-eamcet", "chemistry", "redox-reactions", "easy", "The oxidation state of Mn in KMnO₄ is:", ["+2", "+4", "+6", "+7"], 3, "+1 + x + 4(−2) = 0 gives x = +7."),
  mcq("iat", "biology", "evolution", "easy", "Homologous organs indicate:", ["Convergent evolution", "Divergent evolution", "No evolution", "Mutation only"], 1, "Homologous organs share a structural origin but differ in function, showing divergence from a common ancestor."),
  mcq("neet", "biology", "plant-physiology", "easy", "The primary CO₂ acceptor in C₃ plants is:", ["PEP", "RuBP", "OAA", "PGA"], 1, "Ribulose-1,5-bisphosphate accepts CO₂ in the Calvin cycle, catalysed by RuBisCO."),
  mcq("neet", "biology", "human-physiology", "easy", "Which blood cells carry oxygen?", ["Leucocytes", "Erythrocytes", "Platelets", "Lymphocytes"], 1, "Erythrocytes (red blood cells) contain haemoglobin, which binds oxygen."),
  mcq("neet", "biology", "molecular-basis-of-inheritance", "medium", "In DNA, adenine pairs with:", ["Guanine", "Cytosine", "Thymine", "Uracil"], 2, "A pairs with T by two hydrogen bonds; uracil replaces thymine only in RNA."),
  mcq("neet", "biology", "ecology", "easy", "In a food chain, herbivores are:", ["Producers", "Primary consumers", "Secondary consumers", "Decomposers"], 1, "Herbivores eat producers directly, so they are primary consumers."),
  mcq("neet", "biology", "biotechnology", "medium", "Restriction enzymes cut DNA at:", ["Random sites", "Specific palindromic sequences", "Only the ends", "RNA primers"], 1, "Type II restriction enzymes recognise specific, usually palindromic, base sequences."),
  mcq("neet", "biology", "human-health-and-disease", "easy", "Malaria is caused by:", ["Bacterium", "Virus", "Plasmodium (a protozoan)", "Fungus"], 2, "Plasmodium, spread by female Anopheles mosquitoes, causes malaria."),
  num("neet", "physics", "laws-of-motion", "easy", "A 10 kg body accelerates at 2 m/s². Find the net force in N.", 20, "F = ma = 10 × 2 = 20 N."),
  num("neet", "chemistry", "some-basic-concepts-of-chemistry", "easy", "Find the molar mass of CO₂ in g/mol (C = 12, O = 16).", 44, "12 + 2 × 16 = 44 g/mol."),
  mcq("aiims", "biology", "cell-structure", "easy", "The powerhouse of the cell is the:", ["Nucleus", "Mitochondrion", "Ribosome", "Vacuole"], 1, "Mitochondria produce most of the cell's ATP by aerobic respiration."),
  mcq("jipmer", "chemistry", "chemical-bonding-and-molecular-structure", "easy", "The bond angle in a water molecule is about:", ["90°", "104.5°", "109.5°", "120°"], 1, "Two lone pairs on oxygen compress the tetrahedral angle to about 104.5°."),
  mcq("mht-cet-pcb", "biology", "genetics", "easy", "The unit of heredity is the:", ["Cell", "Gene", "Ribosome", "Protein"], 1, "Genes are DNA segments that carry hereditary information."),
  mcq("gate-cse", "operating-systems", "deadlocks", "medium", "Which condition is NOT necessary for deadlock?", ["Mutual exclusion", "Hold and wait", "Preemption", "Circular wait"], 2, "Deadlock needs NO preemption; allowing preemption breaks one of the four Coffman conditions."),
  mcq("gate-cse", "dbms", "normalization", "medium", "A relation in BCNF is always in:", ["1NF only", "2NF but not 3NF", "3NF", "4NF"], 2, "BCNF is stricter than 3NF, so every BCNF relation is also in 3NF; it need not be in 4NF."),
  num("gate-cse", "computer-networks", "ip-addressing", "medium", "How many usable host addresses does a /26 IPv4 subnet have?", 62, "2^(32−26) = 64 addresses, minus network and broadcast = 62."),
  mcq("gate-cse", "theory-of-computation", "regular-languages", "medium", "Which language is NOT regular?", ["a*b*", "Strings with even number of a's", "aⁿbⁿ for n ≥ 0", "(ab)*"], 2, "aⁿbⁿ needs unbounded counting; the pumping lemma shows it is not regular."),
  num("gate-cse", "engineering-mathematics", "linear-algebra", "easy", "Find the trace of the 3×3 identity matrix.", 3, "The trace is the sum of diagonal entries: 1 + 1 + 1 = 3."),
  num("gate-cse", "general-aptitude", "quantitative-aptitude", "easy", "A price rises by 20% and then falls by 20%. Find the net percentage change (use a negative number for a loss).", -4, "1.2 × 0.8 = 0.96, a 4% decrease."),
  mcq("gate-ece", "signals-and-systems", "lti-systems", "medium", "An LTI system is fully characterised by its:", ["Step input", "Impulse response", "DC gain", "Noise figure"], 1, "Output = input convolved with the impulse response, so h(t) defines the LTI system."),
  mcq("gate-ee", "electrical-machines", "transformers", "easy", "A transformer works on the principle of:", ["Self induction", "Mutual induction", "Electrostatics", "Hall effect"], 1, "A changing flux from the primary induces EMF in the secondary: mutual induction."),
  num("gate-me", "strength-of-materials", "stress-and-strain", "easy", "A 1000 N axial load acts on a bar of area 10 mm². Find the stress in N/mm².", 100, "σ = P/A = 1000/10 = 100 N/mm² (MPa)."),
  mcq("gate-ce", "environmental-engineering", "water-treatment", "easy", "Coagulation in water treatment commonly uses:", ["Chlorine", "Alum", "Ozone", "Lime only"], 1, "Alum (aluminium sulphate) neutralises charges on colloids so they settle."),
  mcq("gate-pi", "manufacturing", "welding", "easy", "Which welding process uses a non-consumable tungsten electrode?", ["MIG", "TIG", "SMAW", "Submerged arc"], 1, "TIG (GTAW) uses a tungsten electrode that does not melt into the weld."),
  mcq("gate-in", "measurements", "sensors-and-transducers", "easy", "A thermocouple converts temperature difference into:", ["Resistance", "Voltage", "Capacitance", "Pressure"], 1, "The Seebeck effect produces a voltage between two junctions at different temperatures."),
  mcq("gate-da", "machine-learning", "regression", "easy", "Linear regression trained with ordinary least squares minimises:", ["Absolute error", "Sum of squared errors", "Cross-entropy", "Hinge loss"], 1, "OLS chooses weights that minimise the sum of squared residuals."),
  mcq("upsc-prelims", "general-studies", "indian-polity", "easy", "Fundamental Rights are in which Part of the Indian Constitution?", ["Part II", "Part III", "Part IV", "Part V"], 1, "Part III (Articles 12–35) contains the Fundamental Rights."),
  mcq("upsc-prelims", "general-studies", "geography", "easy", "The Tropic of Cancer does NOT pass through which Indian state?", ["Gujarat", "Rajasthan", "Odisha", "Mizoram"], 2, "It crosses Gujarat, Rajasthan, MP, Chhattisgarh, Jharkhand, West Bengal, Tripura and Mizoram, not Odisha."),
  num("upsc-prelims", "csat", "basic-numeracy", "easy", "What is 15% of 240?", 36, "0.15 × 240 = 36."),
  num("nda", "mathematics", "trigonometric-ratio-and-identities", "easy", "Find sin²30° + cos²30° .", 1, "sin²θ + cos²θ = 1 for every angle."),
  mcq("nda", "general-ability", "history", "easy", "The Battle of Plassey was fought in:", ["1757", "1764", "1857", "1526"], 0, "Robert Clive's forces defeated Siraj-ud-Daulah at Plassey in 1757."),
  num("ssc-cgl", "quantitative-aptitude", "time-and-work", "medium", "A can do a job in 10 days and B in 15 days. Working together, how many days do they take?", 6, "Combined rate = 1/10 + 1/15 = 1/6, so 6 days."),
  num("ssc-cgl", "quantitative-aptitude", "profit-and-loss", "easy", "An item bought for ₹400 is sold for ₹500. Find the profit percentage.", 25, "Profit = 100; 100/400 × 100 = 25%."),
  num("ssc-cgl", "general-intelligence-and-reasoning", "series", "easy", "Find the next number: 2, 6, 12, 20, 30, ?", 42, "Differences are 4, 6, 8, 10, 12, so 30 + 12 = 42."),
  mcq("ssc-cgl", "english-comprehension", "vocabulary", "easy", "Choose the synonym of 'abundant':", ["Scarce", "Plentiful", "Tiny", "Rare"], 1, "Abundant means existing in large quantities: plentiful."),
  mcq("cbse-12", "chemistry", "electrochemistry", "easy", "In a galvanic cell, oxidation occurs at the:", ["Cathode", "Anode", "Salt bridge", "Both electrodes"], 1, "Oxidation always happens at the anode."),
  num("cbse-12", "mathematics", "matrices", "easy", "If A is a 2×3 matrix and B is 3×4, how many elements does AB have?", 8, "AB is 2×4, which has 8 elements."),
  num("cbse-10", "mathematics", "arithmetic-progressions", "easy", "Find the sum of the first 10 terms of the AP 1, 3, 5, …", 100, "Sum of the first n odd numbers is n² = 100."),
  mcq("cbse-10", "science", "electricity", "easy", "The SI unit of electric current is:", ["Volt", "Ohm", "Ampere", "Watt"], 2, "Current is measured in amperes."),
  num("icse-10", "physics", "light", "easy", "The refractive index of glass is 1.5. Find the speed of light in glass in units of 10⁸ m/s (c = 3 × 10⁸ m/s).", 2, "v = c/n = 3/1.5 = 2 × 10⁸ m/s."),
  // Original Units & Measurements practice; append to preserve all existing question IDs.
  mcq("jee-main", "physics", "units-and-measurements", "easy", "Which dimensional formula represents pressure?", ["[MLT⁻²]", "[ML⁻¹T⁻²]", "[ML²T⁻²]", "[M⁻¹LT⁻²]"], 1, "Pressure is force per area: [MLT⁻²]/[L²] = [ML⁻¹T⁻²]."),
  mcq("jee-main", "physics", "units-and-measurements", "medium", "The dimensions of Planck's constant h are:", ["[MLT⁻¹]", "[ML²T⁻¹]", "[ML²T⁻²]", "[M⁰L²T⁻¹]"], 1, "E = hν, so [h] = [energy]/[frequency] = [ML²T⁻²]/[T⁻¹] = [ML²T⁻¹]."),
  mcq("jee-main", "physics", "units-and-measurements", "easy", "A circle's radius has a maximum percentage error of 3%. What is the approximate maximum percentage error in its calculated area?", ["3%", "6%", "9%", "12%"], 1, "Area A = πr². For small measurement errors, percentage error in A is approximately 2 times that in r: 2 × 3% = 6%."),
  mcq("jee-main", "physics", "units-and-measurements", "easy", "Two measured lengths are 12.31 cm and 0.4 cm. Report their sum using the correct decimal-place rule.", ["12.71 cm", "12.7 cm", "13 cm", "12.710 cm"], 1, "The second measurement has one decimal place, so 12.31 + 0.4 = 12.71 cm is reported as 12.7 cm."),
  num("jee-main", "physics", "units-and-measurements", "easy", "A vernier scale has 10 divisions equal to 9 main-scale divisions. If one main-scale division is 1 mm, find the least count in mm.", 0.1, "One vernier division is 0.9 mm. Least count = 1.0 − 0.9 = 0.1 mm."),
  num("jee-main", "physics", "units-and-measurements", "easy", "Convert 54 km/h to m/s. Enter the numerical value.", 15, "Multiply by 1000/3600: 54 × 5/18 = 15 m/s."),
  num("jee-main", "physics", "units-and-measurements", "medium", "A wire's density is calculated from its mass m, radius r and length L using ρ = m/(πr²L). If their maximum percentage errors are 1%, 2% and 1%, find the approximate maximum percentage error in ρ.", 6, "For products and powers, maximum fractional errors add: Δρ/ρ ≈ Δm/m + 2Δr/r + ΔL/L = 1% + 4% + 1% = 6%."),
];

export const QUESTIONS: Question[] = RAW.map((q, i) => ({
  ...q,
  id: q.id ?? `p2p-q${String(i + 1).padStart(4, "0")}`,
  version: 1,
  year: null,
  shift: null,
}));

export const categoryOf = (e: Exam) => CATEGORIES.find((c) => c.slug === e.category)!;
export const examsIn = (category: string) => EXAMS.filter((e) => e.category === category);
export const examBySlug = (s: string) => EXAMS.find((e) => e.slug === s);
export const subjectOf = (e: Exam, s: string) => e.subjects.find((x) => x.slug === s);
export const chapterName = (sub: Subject, c: string) => sub.chapters.find(([slug]) => slug === c)?.[1];

// Verified against the JEE Main chapter links on ExamSIDE; keep internal IDs stable.
const JEE_MAIN_SLUGS: Record<string, Record<string, string>> = {
  physics: {
    "center-of-mass-and-collision": "center-of-mass",
    "mechanical-properties-of-solids": "elasticity",
    "mechanical-properties-of-fluids": "fluid-mechanics",
    "magnetic-effect-of-current": "magnetics",
    "semiconductor-devices": "electronic-devices",
  },
  mathematics: {
    "trigonometric-ratio-and-identities": "trigonometric-ratio-and-identites",
    "trigonometric-equations": "trigonometric-functions-and-equations",
  },
};
const JEE_MAIN_UNMATCHED = new Set(["chemistry/states-of-matter", "chemistry/chemical-kinetics", "mathematics/application-of-integration"]);
export function jeeMainPublicChapterSlug(subject: string, internal: string): string | null {
  return JEE_MAIN_UNMATCHED.has(`${subject}/${internal}`) ? null : JEE_MAIN_SLUGS[subject]?.[internal] ?? internal;
}
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

// Papers. Only verified, rights-cleared past papers may carry a year/shift.
// Until those exist, each exam gets clearly labelled original practice sets.
export type Paper = { id: string; exam: string; title: string; kind: "past" | "practice"; year: number | null; date: string | null; questionIds: string[] };
export function papersFor(examSlug: string): Paper[] {
  const e = examBySlug(examSlug);
  if (!e) return [];
  const qs = questionsFor(examSlug);
  if (qs.length === 0) return [];
  return [{ id: "practice-set-1", exam: examSlug, title: `${e.name} Practice Set 1`, kind: "practice", year: null, date: null, questionIds: qs.map((q) => q.id) }];
}
export const paperById = (examSlug: string, id: string) => papersFor(examSlug).find((p) => p.id === id);
