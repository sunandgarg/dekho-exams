export type PracticeQuestion = {
  prompt: string;
  choices: [string, string, string, string];
  answer: number;
  explanation: string;
};

export type SchoolLesson = {
  grade: number;
  subject: "Mathematics" | "Science";
  slug: string;
  title: string;
  summary: string;
  keyIdea: string;
  whyItWorks: string;
  commonMistake: string;
  example: string;
  steps: string[];
  check: string;
  questions: PracticeQuestion[];
};

export const GRADES = Array.from({ length: 12 }, (_, index) => index + 1);

export const SCHOOL_LESSONS: SchoolLesson[] = [
  {
    grade: 1,
    subject: "Mathematics",
    slug: "counting-to-20",
    title: "Counting to 20",
    summary: "Count objects in order and connect each group to its number.",
    keyIdea:
      "Each number tells how many objects are in a group. Touch or point to each object once as you count; the last number you say is the total.",
    whyItWorks:
      "Matching one number word to each object makes counting reliable. Once every object has been matched, the final number word names the size of the whole group, no matter which object you started with.",
    commonMistake:
      "Skipping an object or counting the same object twice changes the total. Move counted objects aside, or mark each one as you say its number.",
    example: "There are 8 pencils. Add 3 more. How many pencils are there now?",
    steps: [
      "Start at 8.",
      "Count on three numbers: 9, 10, 11.",
      "There are 11 pencils altogether.",
    ],
    check: "Count the same group again in a different order. The total should stay 11.",
    questions: [
      {
        prompt: "What number comes after 14?",
        choices: ["13", "15", "16", "20"],
        answer: 1,
        explanation: "Count one step forward from 14 to get 15.",
      },
      {
        prompt: "You have 9 crayons and get 2 more. How many now?",
        choices: ["7", "10", "11", "12"],
        answer: 2,
        explanation: "Count on from 9: 10, 11.",
      },
    ],
  },
  {
    grade: 2,
    subject: "Mathematics",
    slug: "tens-and-ones",
    title: "Tens and ones",
    summary: "Read two-digit numbers as groups of ten and single ones.",
    keyIdea:
      "The left digit in a two-digit number counts tens. The right digit counts ones. Ten ones can be bundled into one ten.",
    whyItWorks:
      "Ten individual ones can be exchanged for one group of ten without changing the amount. That exchange is what makes the position of a digit matter in our base-ten system.",
    commonMistake:
      "In 47, the 4 does not mean four single objects. It means four tens, or 40; the 7 represents seven ones.",
    example: "What is the value of 47?",
    steps: ["The 4 means 4 tens, or 40.", "The 7 means 7 ones.", "40 + 7 = 47."],
    check: "If you regroup 10 of the ones into a ten, the number's value does not change.",
    questions: [
      {
        prompt: "What number is 3 tens and 6 ones?",
        choices: ["9", "30", "36", "63"],
        answer: 2,
        explanation: "Three tens are 30; add 6 ones to get 36.",
      },
      {
        prompt: "How many tens are in 82?",
        choices: ["2", "8", "80", "82"],
        answer: 1,
        explanation: "The tens digit is 8.",
      },
    ],
  },
  {
    grade: 3,
    subject: "Mathematics",
    slug: "multiplication-groups",
    title: "Multiplication as equal groups",
    summary: "Use equal groups to understand multiplication facts.",
    keyIdea:
      "Multiplication counts equal groups. Four groups of three means 3 + 3 + 3 + 3, written 4 × 3.",
    whyItWorks:
      "When every group has the same size, repeated addition follows a pattern. Multiplication names that pattern with the number of groups and the number in each group.",
    commonMistake:
      "Do not use one multiplication fact for groups of different sizes without first finding what is in each group. The word equal is the key condition.",
    example: "Five tables each have 4 books. How many books are there?",
    steps: ["There are 5 equal groups.", "Each group has 4 books.", "5 × 4 = 20 books."],
    check: "Repeated addition gives 4 + 4 + 4 + 4 + 4 = 20.",
    questions: [
      {
        prompt: "What is 3 groups of 6?",
        choices: ["9", "12", "18", "36"],
        answer: 2,
        explanation: "6 + 6 + 6 = 18.",
      },
      {
        prompt: "Which expression means 4 groups of 2?",
        choices: ["4 + 2", "4 × 2", "4 − 2", "4 ÷ 2"],
        answer: 1,
        explanation: "Four equal groups of two are written 4 × 2.",
      },
    ],
  },
  {
    grade: 4,
    subject: "Mathematics",
    slug: "equivalent-fractions",
    title: "Equivalent fractions",
    summary: "Recognize fractions that name the same part of a whole.",
    keyIdea:
      "Equivalent fractions have the same value. Multiply the numerator and denominator by the same nonzero number to make an equivalent fraction.",
    whyItWorks:
      "Multiplying both parts of a fraction by the same nonzero number is the same as multiplying its value by one. The pieces become smaller, but more of them are counted, so the portion stays unchanged.",
    commonMistake:
      "Changing only the numerator or only the denominator changes the fraction's value. Check both parts before calling two fractions equivalent.",
    example: "Is 2/3 equal to 4/6?",
    steps: [
      "Multiply the numerator 2 by 2 to get 4.",
      "Multiply the denominator 3 by 2 to get 6.",
      "Both fractions cover the same amount, so 2/3 = 4/6.",
    ],
    check: "Dividing both parts of 4/6 by 2 returns 2/3.",
    questions: [
      {
        prompt: "Which fraction is equivalent to 1/2?",
        choices: ["1/4", "2/4", "2/3", "3/4"],
        answer: 1,
        explanation: "Multiply both 1 and 2 by 2: 1/2 = 2/4.",
      },
      {
        prompt: "What is 3/5 with denominator 10?",
        choices: ["3/10", "5/10", "6/10", "8/10"],
        answer: 2,
        explanation: "Multiply numerator and denominator by 2: 6/10.",
      },
    ],
  },
  {
    grade: 5,
    subject: "Mathematics",
    slug: "decimal-place-value",
    title: "Decimal place value",
    summary: "Understand tenths and hundredths in decimal numbers.",
    keyIdea:
      "The first place after the decimal point is tenths; the second is hundredths. The number 0.35 means 3 tenths and 5 hundredths.",
    whyItWorks:
      "One tenth is ten hundredths. Writing 0.4 as 0.40 shows that four tenths and forty hundredths are the same amount and makes decimal comparisons easier.",
    commonMistake:
      "The digits after a decimal point are not separate whole numbers. In 0.47, the 4 means four tenths, not four ones.",
    example: "Write 4 tenths and 7 hundredths as a decimal.",
    steps: ["Four tenths is 0.4.", "Seven hundredths is 0.07.", "0.4 + 0.07 = 0.47."],
    check: "0.47 is also 47 hundredths.",
    questions: [
      {
        prompt: "What is the value of 6 in 0.62?",
        choices: ["6", "0.6", "0.06", "60"],
        answer: 1,
        explanation: "The 6 is in the tenths place, so its value is 0.6.",
      },
      {
        prompt: "Which is greater?",
        choices: ["0.4", "0.35", "They are equal", "Cannot tell"],
        answer: 0,
        explanation: "Write 0.4 as 0.40; 40 hundredths is greater than 35 hundredths.",
      },
    ],
  },
  {
    grade: 6,
    subject: "Mathematics",
    slug: "adding-fractions",
    title: "Adding fractions",
    summary: "Add fractions by making the parts the same size first.",
    keyIdea:
      "Fractions can be added directly when their denominators match. For different denominators, rename them as equivalent fractions with a common denominator.",
    whyItWorks:
      "Addition combines pieces of the same size. A common denominator gives both fractions equally sized pieces, so their numerators can be added meaningfully.",
    commonMistake:
      "Adding the denominators as well as the numerators gives the wrong size of piece. First make the denominators match, then add only the numerators.",
    example: "Find 1/2 + 1/3.",
    steps: ["Use 6 as a common denominator.", "1/2 = 3/6 and 1/3 = 2/6.", "3/6 + 2/6 = 5/6."],
    check:
      "The answer is less than 1, which makes sense because one half plus one third does not fill a whole.",
    questions: [
      {
        prompt: "What is 1/4 + 2/4?",
        choices: ["3/8", "3/4", "2/4", "1/2"],
        answer: 1,
        explanation: "The parts are already fourths, so add the numerators: 3/4.",
      },
      {
        prompt: "What is 1/2 + 1/4?",
        choices: ["2/6", "1/4", "3/4", "1/8"],
        answer: 2,
        explanation: "1/2 is 2/4; then 2/4 + 1/4 = 3/4.",
      },
    ],
  },
  {
    grade: 6,
    subject: "Science",
    slug: "food-and-nutrients",
    title: "Food and nutrients",
    summary: "Connect nutrients to what the body uses them for.",
    keyIdea:
      "Food contains nutrients with different roles. Carbohydrates and fats supply energy, proteins help build and repair body tissues, and vitamins and minerals support healthy body processes.",
    whyItWorks:
      "Most foods contain a mixture of nutrients rather than a single one. Combining different food groups helps provide a wider range of nutrients for energy, growth and normal body processes.",
    commonMistake:
      "Do not label a food as containing only one nutrient. For example, dal is a useful source of protein but also supplies other nutrients.",
    example: "A lunch has rice, dal, vegetables and curd. Which parts provide different nutrients?",
    steps: [
      "Rice mainly supplies carbohydrates.",
      "Dal supplies protein along with other nutrients.",
      "Vegetables and curd add vitamins, minerals and other nutrients.",
    ],
    check:
      "No single food in this example supplies every nutrient in the same amount. Variety matters.",
    questions: [
      {
        prompt: "Which nutrient helps the body build and repair tissues?",
        choices: ["Protein", "Water", "Carbohydrate", "Salt"],
        answer: 0,
        explanation: "Proteins are needed to build and repair body tissues.",
      },
      {
        prompt: "Why include different food groups in meals?",
        choices: [
          "To avoid drinking water",
          "To get a variety of nutrients",
          "To remove all fats",
          "To stop digestion",
        ],
        answer: 1,
        explanation: "Different foods contribute different nutrients.",
      },
    ],
  },
  {
    grade: 7,
    subject: "Mathematics",
    slug: "integers-on-number-line",
    title: "Integers on a number line",
    summary: "Add and compare positive and negative numbers.",
    keyIdea:
      "Numbers increase as you move right on a number line. Adding a positive number moves right; adding a negative number moves left.",
    whyItWorks:
      "A number line puts each integer in a fixed order. A move to the right increases the value by one for every step; a move to the left decreases it by one.",
    commonMistake:
      "A negative number with a larger-looking digit is not always greater. For example, −7 lies left of −2, so −7 is smaller.",
    example: "Find −3 + 5.",
    steps: ["Start at −3.", "Move 5 places to the right: −2, −1, 0, 1, 2.", "The answer is 2."],
    check: "Because 5 is larger than 3, the result is positive.",
    questions: [
      {
        prompt: "What is −4 + 2?",
        choices: ["−6", "−2", "2", "6"],
        answer: 1,
        explanation: "Move two places right from −4 to reach −2.",
      },
      {
        prompt: "Which number is greatest?",
        choices: ["−7", "−2", "0", "−1"],
        answer: 2,
        explanation: "Zero lies to the right of every negative number.",
      },
    ],
  },
  {
    grade: 8,
    subject: "Mathematics",
    slug: "linear-equations",
    title: "Linear equations in one variable",
    summary: "Solve an equation by keeping both sides balanced.",
    keyIdea:
      "An equation says two expressions are equal. Doing the same operation to both sides preserves equality, so you can isolate the unknown.",
    whyItWorks:
      "An equation is like a balance: if both sides change by the same amount, they remain equal. Inverse operations undo addition or multiplication until the unknown stands alone.",
    commonMistake:
      "Changing only one side breaks the equality. Write each operation on both sides and substitute your answer into the original equation to check it.",
    example: "Solve 3x + 5 = 20.",
    steps: [
      "Subtract 5 from both sides: 3x = 15.",
      "Divide both sides by 3: x = 5.",
      "Check: 3 × 5 + 5 = 20.",
    ],
    check: "Substituting the answer into the original equation is the final check.",
    questions: [
      {
        prompt: "Solve x + 7 = 12.",
        choices: ["3", "5", "7", "19"],
        answer: 1,
        explanation: "Subtract 7 from both sides to get x = 5.",
      },
      {
        prompt: "Solve 2x = 18.",
        choices: ["7", "8", "9", "16"],
        answer: 2,
        explanation: "Divide both sides by 2 to get x = 9.",
      },
    ],
  },
  {
    grade: 9,
    subject: "Mathematics",
    slug: "polynomial-identities",
    title: "Polynomial identities",
    summary: "Expand and check the square of a sum.",
    keyIdea:
      "The identity (a + b)² = a² + 2ab + b² works for any values of a and b. The middle term appears twice when the two brackets are multiplied.",
    whyItWorks:
      "Expanding (a + b)(a + b) produces four products: a², ab, ba and b². The two cross-products are equal, so together they give 2ab.",
    commonMistake:
      "(a + b)² is not a² + b². The two cross-products must be included; test a small value such as a = b = 1 to catch this error.",
    example: "Expand (x + 3)².",
    steps: ["Use a = x and b = 3.", "Write a² + 2ab + b².", "The result is x² + 6x + 9."],
    check: "At x = 2, both (2 + 3)² and 2² + 6 × 2 + 9 equal 25.",
    questions: [
      {
        prompt: "Expand (x + 2)².",
        choices: ["x² + 4", "x² + 2x + 4", "x² + 4x + 4", "2x² + 4"],
        answer: 2,
        explanation: "Use x² + 2 × x × 2 + 2² = x² + 4x + 4.",
      },
      {
        prompt: "What is the middle term in (a + 5)²?",
        choices: ["5a", "10a", "25a", "a²"],
        answer: 1,
        explanation: "The middle term is 2 × a × 5 = 10a.",
      },
    ],
  },
  {
    grade: 10,
    subject: "Mathematics",
    slug: "quadratic-equations",
    title: "Quadratic equations by factorisation",
    summary: "Solve a quadratic by finding factors and checking both roots.",
    keyIdea:
      "A quadratic equation has a squared variable. If a product equals zero, at least one factor must be zero; this turns a factorised quadratic into simpler equations.",
    whyItWorks:
      "The zero-product rule says that if two factors multiply to zero, one or both factors must be zero. After moving every term to one side, factor the quadratic and solve each resulting linear equation. Substituting each root into the original expression confirms it.",
    commonMistake:
      "Do not apply the zero-product rule while the right side is nonzero. Watch the signs when choosing factors: for x² − 5x + 6, the numbers must multiply to +6 and add to −5.",
    example: "Solve x² − 5x + 6 = 0.",
    steps: [
      "Find two numbers whose product is 6 and sum is −5: −2 and −3.",
      "Factor: (x − 2)(x − 3) = 0.",
      "Set each factor to zero. The roots are x = 2 and x = 3.",
    ],
    check: "Substitute 2 and 3 into x² − 5x + 6; each gives 0.",
    questions: [
      {
        prompt: "What are the roots of x² − 4x + 3 = 0?",
        choices: ["1 and 3", "−1 and −3", "2 and 2", "0 and 3"],
        answer: 0,
        explanation: "(x − 1)(x − 3) = 0, so x is 1 or 3.",
      },
      {
        prompt: "If (x − 5)(x + 2) = 0, which values solve it?",
        choices: ["5 and 2", "−5 and 2", "5 and −2", "−5 and −2"],
        answer: 2,
        explanation: "Set each factor to zero: x = 5 or x = −2.",
      },
    ],
  },
  {
    grade: 10,
    subject: "Science",
    slug: "electric-circuits",
    title: "Current, voltage and resistance",
    summary: "Use Ohm's law for a simple circuit and keep units visible.",
    keyIdea:
      "Electric current is the rate of charge flow. Potential difference pushes charge around a circuit, and resistance opposes current. For an ohmic conductor at constant temperature, V = IR.",
    whyItWorks:
      "For an ohmic conductor under constant physical conditions, voltage and current are proportional. Dividing voltage by resistance therefore gives current, and the units V/Ω simplify to amperes.",
    commonMistake:
      "Keep units in every calculation and check that the material behaves approximately ohmically. A changing temperature can change resistance, so V = IR is not a claim that every component has a fixed resistance.",
    example: "A 3 Ω resistor has 6 V across it. What current flows?",
    steps: ["Start with V = IR.", "Rearrange to I = V/R.", "Substitute: I = 6 V / 3 Ω = 2 A."],
    check:
      "Multiplying 2 A by 3 Ω returns 6 V. The relation may not stay linear when temperature changes.",
    questions: [
      {
        prompt: "A 4 Ω resistor carries 2 A. What is the voltage?",
        choices: ["2 V", "4 V", "6 V", "8 V"],
        answer: 3,
        explanation: "V = IR = 2 A × 4 Ω = 8 V.",
      },
      {
        prompt: "What is the SI unit of resistance?",
        choices: ["Ampere", "Volt", "Ohm", "Watt"],
        answer: 2,
        explanation: "Resistance is measured in ohms (Ω).",
      },
    ],
  },
  {
    grade: 11,
    subject: "Mathematics",
    slug: "sets-and-intersection",
    title: "Sets and intersection",
    summary: "Describe collections and find elements shared by two sets.",
    keyIdea:
      "A set is a well-defined collection of distinct elements. The intersection A ∩ B contains only elements that belong to both A and B.",
    whyItWorks:
      "Intersection applies the word and: an element must pass the membership test for A and for B. Checking both conditions excludes elements that appear in only one set.",
    commonMistake:
      "Do not confuse intersection with union. Union includes elements from either set; intersection keeps only those shared by both.",
    example: "Let A = {1, 2, 3, 4} and B = {3, 4, 5}. Find A ∩ B.",
    steps: [
      "List the elements of A.",
      "Check which of them also appear in B: 3 and 4.",
      "A ∩ B = {3, 4}.",
    ],
    check: "Neither 1 nor 5 belongs to both sets, so neither belongs in the intersection.",
    questions: [
      {
        prompt: "What is {a, b, c} ∩ {b, d}?",
        choices: ["{a, b, c, d}", "{b}", "{a, c}", "{}"],
        answer: 1,
        explanation: "Only b appears in both sets.",
      },
      {
        prompt: "Which statement is true for A ∩ B?",
        choices: [
          "Every element is in both A and B",
          "Every element is in A only",
          "It always equals A",
          "Duplicates are counted twice",
        ],
        answer: 0,
        explanation: "Intersection keeps the elements shared by both sets.",
      },
    ],
  },
  {
    grade: 12,
    subject: "Mathematics",
    slug: "derivatives-from-first-principles",
    title: "Derivative from first principles",
    summary: "Find the rate of change of x² using a limit.",
    keyIdea:
      "The derivative at x measures the limiting slope between two nearby points. For f(x), use the limit of [f(x + h) − f(x)]/h as h approaches 0, when that limit exists.",
    whyItWorks:
      "The quotient measures the slope between the points at x and x + h. As h approaches zero, those points approach one another; if the slopes approach a single value, that limit is the tangent slope.",
    commonMistake:
      "Do not substitute h = 0 into the original quotient, because it divides by zero. Simplify for nonzero h first, then take the limit.",
    example: "Find the derivative of f(x) = x².",
    steps: [
      "Compute f(x + h) = x² + 2xh + h².",
      "Subtract f(x) and divide by h (for h ≠ 0): 2x + h.",
      "Take the limit as h approaches 0: f′(x) = 2x.",
    ],
    check: "At x = 3 the tangent slope is 6. Never substitute h = 0 before canceling h.",
    questions: [
      {
        prompt: "For f(x) = x², what is f′(3)?",
        choices: ["3", "6", "9", "12"],
        answer: 1,
        explanation: "f′(x) = 2x, so f′(3) = 6.",
      },
      {
        prompt: "Why do we simplify before taking h → 0?",
        choices: [
          "To change the function",
          "The quotient initially has h in the denominator",
          "To make h equal 1",
          "Limits cannot use fractions",
        ],
        answer: 1,
        explanation: "Directly setting h = 0 in the original quotient would divide by zero.",
      },
    ],
  },
];

export function lessonsForGrade(grade: number) {
  return SCHOOL_LESSONS.filter((lesson) => lesson.grade === grade);
}

export function lessonPath(lesson: SchoolLesson) {
  return `/class-${lesson.grade}/${lesson.subject === "Mathematics" ? "maths" : "science"}/${lesson.slug}`;
}
