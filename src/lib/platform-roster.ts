export type RosterRow = { name: string; mobile: string; email?: string; level?: string };

export const ROSTER_LIMIT = 250;
const FILE_LIMIT = 1_048_576;

export function parseRosterCsv(source: string): string[][] {
  const table: string[][] = [];
  let row: string[] = [];
  let cell = "";
  let quoted = false;
  let closedQuote = false;
  const finishCell = () => {
    row.push(cell);
    if (row.length > 40) throw new Error("Use a roster with at most 40 columns.");
    cell = "";
    closedQuote = false;
  };
  const finishRow = () => {
    finishCell();
    if (row.some((value) => value.trim())) table.push(row);
    if (table.length > ROSTER_LIMIT + 1) throw new Error("Use at most 250 students per file.");
    row = [];
  };

  const text = source.replace(/^\uFEFF/, "");
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') {
        cell += '"';
        i++;
      } else if (ch === '"') {
        quoted = false;
        closedQuote = true;
      } else cell += ch;
    } else if (ch === ",") {
      finishCell();
    } else if (ch === "\r" || ch === "\n") {
      if (ch === "\r" && text[i + 1] === "\n") i++;
      finishRow();
    } else if (ch === '"' && !cell && !closedQuote) {
      quoted = true;
    } else if (ch === '"' || closedQuote) {
      throw new Error("Check the quotation marks in your CSV file.");
    } else cell += ch;
  }
  if (quoted) throw new Error("A quoted CSV cell is missing its closing quotation mark.");
  if (row.length || cell || closedQuote) finishRow();
  return table;
}

const headerKeys: Record<string, keyof RosterRow> = {
  name: "name",
  fullname: "name",
  studentname: "name",
  mobile: "mobile",
  phone: "mobile",
  mobilenumber: "mobile",
  phonenumber: "mobile",
  email: "email",
  emailaddress: "email",
  level: "level",
  class: "level",
  grade: "level",
};

export function normalizeRosterCells(table: unknown[][]): RosterRow[] {
  const [headers, ...data] = table;
  if (!headers?.length) throw new Error("Add a header row with name and mobile.");
  if (headers.length > 40) throw new Error("Use a roster with at most 40 columns.");
  const keys = headers.map((header) => {
    const key = String(header ?? "")
      .toLowerCase()
      .replace(/[^a-z]/g, "");
    return Object.hasOwn(headerKeys, key) ? headerKeys[key] : undefined;
  });
  const known = keys.filter(Boolean);
  if (!keys.includes("name") || !keys.includes("mobile") || new Set(known).size !== known.length)
    throw new Error(
      "Include one name column and one mobile column. Optional columns are email and class.",
    );
  const rows: RosterRow[] = [];
  for (const [index, cells] of data.entries()) {
    if (!cells.some((value) => value !== null && value !== undefined && String(value).trim()))
      continue;
    const row: RosterRow = { name: "", mobile: "" };
    for (const [column, key] of keys.entries()) {
      if (!key) continue;
      const value = cells[column];
      if (value == null || value === "") continue;
      if (typeof value !== "string" && typeof value !== "number")
        throw new Error(`Check the ${key} value in row ${index + 2}.`);
      row[key] = String(value).trim();
    }
    row.mobile = row.mobile.replace(/[\s()-]/g, "");
    if (/^[6-9]\d{9}$/.test(row.mobile)) row.mobile = "+91" + row.mobile;
    else if (/^91[6-9]\d{9}$/.test(row.mobile)) row.mobile = "+" + row.mobile;
    if (row.level) row.level = row.level.toLowerCase().replace(/^(class|grade)\s*/, "");
    if (!row.name || row.name.length > 120 || !/^\+91[6-9]\d{9}$/.test(row.mobile))
      throw new Error(`Row ${index + 2} needs a student name and a valid Indian mobile number.`);
    if (row.email && (row.email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(row.email)))
      throw new Error(`Check the email address in row ${index + 2}.`);
    if (row.level && !["10", "11", "12", "graduation", "masters"].includes(row.level))
      throw new Error(`Choose class 10, 11, 12, graduation or masters in row ${index + 2}.`);
    rows.push(row);
    if (rows.length > ROSTER_LIMIT) throw new Error("Use at most 250 students per file.");
  }
  if (!rows.length) throw new Error("The roster does not contain any students.");
  return rows;
}

// Check normal XLSX archive limits before the isolated parser expands the file.
function checkXlsxSize(bytes: ArrayBuffer) {
  const zip = new DataView(bytes);
  let end = zip.byteLength - 22;
  for (; end >= Math.max(0, zip.byteLength - 65_557); end--) {
    if (
      zip.getUint32(end, true) === 0x06054b50 &&
      end + 22 + zip.getUint16(end + 20, true) === zip.byteLength
    )
      break;
  }
  if (end < Math.max(0, zip.byteLength - 65_557)) throw new Error("Choose a valid .xlsx workbook.");
  const count = zip.getUint16(end + 10, true);
  const size = zip.getUint32(end + 12, true);
  let cursor = zip.getUint32(end + 16, true);
  if (
    count < 1 ||
    count > 100 ||
    cursor + size !== end ||
    zip.getUint16(end + 4, true) ||
    zip.getUint16(end + 6, true) ||
    zip.getUint16(end + 8, true) !== count
  )
    throw new Error("Use a small, unprotected Excel workbook.");
  let expanded = 0;
  for (let i = 0; i < count; i++) {
    if (cursor + 46 > end || zip.getUint32(cursor, true) !== 0x02014b50)
      throw new Error("Choose a valid .xlsx workbook.");
    expanded += zip.getUint32(cursor + 24, true);
    if (expanded > 8 * 1_048_576) throw new Error("Use a small workbook with one class roster.");
    cursor +=
      46 +
      zip.getUint16(cursor + 28, true) +
      zip.getUint16(cursor + 30, true) +
      zip.getUint16(cursor + 32, true);
  }
  if (cursor !== end) throw new Error("Choose a valid .xlsx workbook.");
}

export async function readRoster(file: File): Promise<RosterRow[]> {
  if (!file.size || file.size > FILE_LIMIT)
    throw new Error("Choose a file between 1 byte and 1 MB.");
  if (/\.csv$/i.test(file.name)) return normalizeRosterCells(parseRosterCsv(await file.text()));
  if (/\.xlsx$/i.test(file.name)) {
    checkXlsxSize(await file.arrayBuffer());
    const { readSheet } = await import("read-excel-file/browser");
    return normalizeRosterCells(await readSheet(file, 1));
  }
  throw new Error("Choose a CSV or .xlsx file. Save older .xls files as .xlsx first.");
}
