export const pdfExams: Record<string, string> = {
  "jee-main": "JEE Main",
  "jee-advanced": "JEE Advanced",
  bitsat: "BITSAT",
  viteee: "VITEEE",
  comedk: "COMEDK",
  "mht-cet": "MHT CET",
  wbjee: "WBJEE",
  "ap-eapcet": "AP EAPCET",
};
export type PdfEntry = {
  path: string;
  title: string;
  subject: string;
  year: number;
  kind: string;
  pages: number;
  questions: number;
  years: string;
  shift: string;
  sourceType: string;
  date: string;
  file: string;
};
