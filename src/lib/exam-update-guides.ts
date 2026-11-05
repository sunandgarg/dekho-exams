export type OfficialLink = { title: string; path: string };
export type ExamGuide = {
  path: string;
  title: string;
  description: string;
  sections: { heading: string; guidance: string; links: OfficialLink[] }[];
};

export const EXAM_GUIDES: ExamGuide[] = [
  {
    path: "/exam-updates/date-sheets",
    title: "CBSE Class 10 and 12 Date Sheets",
    description:
      "Find the official CBSE Class 10 and Class 12 board exam date sheet, revised schedules and examination circulars. Verify the year and revision on CBSE before planning.",
    sections: [
      {
        heading: "CBSE Class 10 and 12 board exam date sheet",
        guidance:
          "CBSE publishes date sheets and revisions in its examination circulars. Open the circular for your examination year and check its issue date before downloading the PDF.",
        links: [{ title: "CBSE examination circulars", path: "https://www.cbse.gov.in/cbsenew/examination_circular.html" }],
      },
    ],
  },
  {
    path: "/exam-updates/answer-keys",
    title: "JEE Main and NEET Answer Keys",
    description:
      "Check JEE Main and NEET provisional and final answer key notices on the official NTA exam portals. Confirm your session, paper and challenge window there.",
    sections: [
      {
        heading: "JEE Main answer key",
        guidance:
          "Use the JEE Main portal for session-specific provisional or final keys. If a challenge window is open, follow only the current instructions on the official portal.",
        links: [{ title: "JEE Main official portal", path: "https://jeemain.nta.nic.in/" }],
      },
      {
        heading: "NEET UG answer key",
        guidance:
          "Use the NEET portal for the relevant examination year's answer key and notices. A provisional key can change after challenges are reviewed.",
        links: [{ title: "NEET UG official portal", path: "https://neet.nta.nic.in/" }],
      },
      {
        heading: "NTA notices",
        guidance: "NTA's notice archive helps you confirm the publication date and whether a newer notice supersedes an earlier one.",
        links: [{ title: "NTA notice archive", path: "https://nta.ac.in/NoticeBoardArchive" }],
      },
    ],
  },
  {
    path: "/exam-updates/results",
    title: "CBSE, JEE Main and NEET Results",
    description:
      "Go to official CBSE and NTA result portals for Class 10, Class 12, JEE Main and NEET. Pencil2Pen does not collect roll numbers, dates of birth or login credentials.",
    sections: [
      {
        heading: "CBSE Class 10 and Class 12 results",
        guidance:
          "The CBSE results portal lists available result sessions. Select your class and year on that site; keep your credentials on the official portal only.",
        links: [{ title: "CBSE results portal", path: "https://www.cbseresults.nic.in/" }],
      },
      {
        heading: "JEE Main result",
        guidance: "Check the JEE Main portal for the current session's scorecard and result notice.",
        links: [{ title: "JEE Main official portal", path: "https://jeemain.nta.nic.in/" }],
      },
      {
        heading: "NEET UG result",
        guidance: "Check the NEET portal for the current examination year's result notice and scorecard access.",
        links: [{ title: "NEET UG official portal", path: "https://neet.nta.nic.in/" }],
      },
    ],
  },
  {
    path: "/exam-updates/marking-schemes",
    title: "CBSE Sample Papers and Marking Schemes 2026-27",
    description:
      "Open official CBSE Class 10 and Class 12 sample question papers and marking schemes for 2026-27. These are preparation materials, not board exam answer keys.",
    sections: [
      {
        heading: "Class 10 sample papers and marking schemes",
        guidance: "Choose your subject and check both the sample question paper and its marking scheme on CBSE Academic.",
        links: [{ title: "CBSE Class 10 SQP and MS 2026-27", path: "https://cbseacademic.nic.in/SQP_CLASSX_2026-27.html" }],
      },
      {
        heading: "Class 12 sample papers and marking schemes",
        guidance: "Use the Class 12 subject list on CBSE Academic and check the course variant that applies to you.",
        links: [{ title: "CBSE Class 12 SQP and MS 2026-27", path: "https://cbseacademic.nic.in/SQP_CLASSXII_2026-27.html" }],
      },
    ],
  },
];

export function examGuide(path: string) {
  return EXAM_GUIDES.find((guide) => guide.path === path);
}
