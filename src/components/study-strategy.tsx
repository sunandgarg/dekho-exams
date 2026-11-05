export function StudyStrategy({ lesson = false, subject = "" }: { lesson?: boolean; subject?: string }) {
  const language = ["english", "hindi"].includes(subject.toLowerCase());
  const maths = ["maths", "mathematics"].includes(subject.toLowerCase());
  const habit = lesson
    ? "Work through the example once without looking. If you get stuck, mark the step and come back to it."
    : language
      ? "Read one paragraph aloud. Close the book and say what it meant in your own words."
      : maths
        ? "Try one problem on paper before reading the solution. Keep the bit where you got stuck."
        : "Pick one thing to work on. Jot down what you already know before opening another page, even if it is only a little.";
  const slip = lesson
    ? "Easy slip: checking the answer too soon. Give yourself one honest try first."
    : language
      ? "Easy slip: reading the same line again without taking it in. Pause and retell it."
      : maths
        ? "Easy slip: rushing to a formula before reading what the question asks. Circle the unknown first."
        : "Easy slip: opening five topics and finishing none. One is enough for today.";
  return (
    <section className="study-strategy" id="study-strategy" aria-labelledby="study-strategy-title">
      <div className="study-strategy-heading">
        <h2 id="study-strategy-title">{lesson ? "Try it on paper" : "A small way to start"}</h2>
      </div>
      <p>{habit}</p>
      <p className="study-strategy-slip">{slip}</p>
    </section>
  );
}
