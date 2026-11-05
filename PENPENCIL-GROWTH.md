# Pencil2Pen launch and growth roadmap

## Goal and current baseline

The aspiration is 1 million daily visits. That is roughly 30 million visits in a 30-day month. No code change or SEO setting can guarantee it. Measure daily organic visits, returning learners, lesson completion, practice accuracy, and page speed before setting growth forecasts.

The current student release is a small foundation: one original maths lesson for each Class 1–12, plus science lessons for Classes 6 and 10. Each has a worked example and two explained practice questions. The existing programming library remains available. Do not describe this as complete NCERT, CBSE, JEE or NEET coverage.

## Audience and content structure

Primary audience: Indian school students and the adults helping them. The first content pillars should be class-based maths and science, followed by English and social science where the team has qualified reviewers. A second pillar can cover Class 11–12 exam preparation after the foundational school library is useful. Keep programming in a separate computing area.

Use stable paths: `/study/class-{grade}/{topic}`. The next level of expansion should add subject and chapter hubs once there are several substantial lessons per subject. A new page needs a distinct learning objective, correct explanation, worked example, misconceptions, accessible practice, and editorial review. Do not create empty class/subject/chapter combinations just to grow the URL count.

## Editorial workflow

1. Map topics against the current board syllabus and record board, class, subject, chapter, edition, reviewer and last review date in the CMS.
2. Write original explanations and questions. Have a subject expert check facts, solutions, age suitability and wording before publication.
3. Test each question's correct choice and explanation. Check internal links, mobile rendering and reading order.
4. Update a lesson when the syllabus or a worked answer changes; show a real review date rather than resetting dates for appearance.

The inherited WordPress content API can publish reviewed entries, but its current AITrove branding, legacy content and production configuration need a separate migration review before using it for school publishing.

## Discovery and distribution

- Keep one canonical URL per lesson, server-render lesson text, include reviewed pages in XML sitemaps, and submit the production sitemap in Google Search Console.
- Track Search Console queries and indexing by class, subject and chapter. Build related lessons where learners actually need them, then link from class hubs and prerequisite lessons.
- Build free teacher-friendly worksheets and revision sets only after answer checking and usage rights are clear. Invite educators to review and share genuinely useful resources.
- Test direct, school-community and video distribution without making traffic claims. Avoid collecting children's personal information until a reviewed privacy policy and suitable safeguards are in place.
- Keep search result pages and unfinished content out of the index. Do not add Course rich-result markup to single lessons; Google's Course definition requires an actual course structure and instructor context.

## Release gates

| Phase | Product work | Evidence to watch |
| --- | --- | --- |
| First month | Verify domain and CMS ownership; review branding/legal pages; publish a coherent set of complete maths chapters for 2–3 grades; add production analytics with privacy review. | Index coverage, errors, learning completion, question feedback. |
| Months 2–3 | Expand chapter coverage, add expert reviews, worksheet formats and prerequisite links. | Organic landing pages, return visits, teacher feedback, page speed. |
| Months 4–6 | Broaden to more grades/subjects only where editorial capacity exists; improve search and content tools. | Search Console query growth, lesson quality checks, repeat use. |
| Later | Consider exam prep, languages and partnerships based on measured demand and educational quality. | Sustained engaged visits, not page count alone. |

Before public indexing, point `VITE_SITE_URL` at the live `https://pencil2pen.com` origin, complete production hosting and DNS, review the privacy policy and all inherited pages, then set `VITE_PREVIEW_MODE=false`. The preview intentionally stays `noindex` today. Check actual responses for canonical tags, sitemap URLs, robots headers and 404s after deployment. The local build does not deploy or configure the domain.

Google's own guidance emphasizes [people-first content](https://developers.google.com/search/docs/fundamentals/creating-helpful-content), [crawlable site structure and sitemaps](https://developers.google.com/search/docs/crawling-indexing), and [structured data that matches visible content](https://developers.google.com/search/docs/appearance/structured-data/sd-policies).
