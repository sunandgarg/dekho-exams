import assert from "node:assert/strict";
import test from "node:test";
import {
  blankPreviewAnswers,
  previewQuestions,
  previewResult,
} from "../src/components/student/preview-diagnostic-data.ts";

test("the diagnostic gives six scorable questions across three subjects", () => {
  const questions = previewQuestions.map(({ choiceKey }) => String(choiceKey));
  const allCorrect = previewResult(questions);
  assert.equal(allCorrect.score, 24);
  assert.equal(allCorrect.accuracy, 100);
  assert.equal(allCorrect.next, undefined);
  assert.deepEqual(
    allCorrect.subjects.map(({ hits }) => hits),
    [2, 2, 2],
  );
  const allSkipped = previewResult(blankPreviewAnswers());
  assert.equal(allSkipped.accuracy, null);
  assert.equal(allSkipped.skipped, 6);
  assert.equal(allSkipped.next?.index, 0);
});

test("wrong and skipped answers are reported separately and the report recommends the first missed topic", () => {
  const result = previewResult(["2", "0", "", "1", "", ""]);
  assert.equal(result.score, 7);
  assert.equal(result.penalty, 1);
  assert.equal(result.accuracy, 67);
  assert.equal(result.skipped, 3);
  assert.equal(result.rows[2].outcome, "Skipped");
  assert.equal(result.next?.question.topic, "Limiting reagents");
});
