import { test } from "node:test";
import assert from "node:assert/strict";
import { normalizeRosterCells, parseRosterCsv, readRoster } from "../src/lib/platform-roster.ts";

test("a roster handles quoted CSV names, aliases, and Indian phone formats", () => {
  const rows = normalizeRosterCells(
    parseRosterCsv(
      '\uFEFFFull Name,Phone Number,Email Address,Grade,Unneeded\r\n"Tester, One",98765-00000,person@example.com,Class 12,ignored\r\n"Tester ""Two""",919876500001,,,x',
    ),
  );
  assert.deepEqual(rows, [
    { name: "Tester, One", mobile: "+919876500000", email: "person@example.com", level: "12" },
    { name: 'Tester "Two"', mobile: "+919876500001" },
  ]);
});

test("a roster rejects incomplete headers, invalid rows and oversized batches", () => {
  assert.throws(() => parseRosterCsv('name,mobile\n"test,9876500000'), /closing/);
  assert.throws(
    () =>
      normalizeRosterCells([
        ["name", "mobile", "phone"],
        ["Test", "9876500000"],
      ]),
    /one name/,
  );
  assert.throws(
    () =>
      normalizeRosterCells([
        ["name", "mobile"],
        ["Test", 123],
      ]),
    /row 2/i,
  );
  assert.throws(
    () =>
      normalizeRosterCells(
        Array.from({ length: 252 }, (_, index) =>
          index ? ["Test", 9876500000] : ["name", "mobile"],
        ),
      ),
    /at most 250/,
  );
});

test("file import reads CSV and rejects malformed Excel before invoking its worker", async () => {
  assert.deepEqual(await readRoster(new File(["name,mobile\nSample,9876500000"], "roster.csv")), [
    { name: "Sample", mobile: "+919876500000" },
  ]);
  await assert.rejects(readRoster(new File(["not a ZIP"], "roster.xlsx")), /valid .xlsx/);
  await assert.rejects(readRoster(new File(["not an .xlsx"], "roster.xls")), /Choose a CSV/);
});
