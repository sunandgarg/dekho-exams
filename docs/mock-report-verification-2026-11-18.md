# Mock report release verification · 18 November 2026

Implementation: `2f961cc8`, deployed to the existing 1 GB Lightsail app and production Cloudflare Worker. Worker version `7b1b5cf9-1913-401d-83bb-b385975bee28`; public cache revision v16. No database migrations, infrastructure upgrades, new answer keys or new images in this release.

## Behaviour

JEE Main and Advanced share the results view. Scored-only attempts exclude review-flagged questions but retain original question numbering. Full-paper review remains available; its previous session-storage key is preserved. Submission and time expiry reveal every question in the attempt, choices, the learner answer, the available verified key and the available solution. Answers appear in the right column on desktop and below each question on mobile.

Downloads are self-contained HTML reports with the approved logo, image bytes and referenced MathJax glyph paths embedded. The same report can be printed or saved as PDF through the browser print dialog. The report contains no scripts, and its content security policy disallows external resources. It does not create a server-side learner record or upload the student's answers.

The practice-readiness meter is `max(0, net score) / available practice marks`, rounded to a whole percentage. It is expressly not a selection probability. The report states how many of the source questions were scorable; zero-key full reviews show “Not graded” and no meter. Practice scoring remains +4/−1, with exact multiple-choice sets and no partial credit, rather than the official year-specific scheme.

## Checks

- TypeScript, production Node build, 19 education checks, 7 edge-media checks, and the Advanced archive/mock grading checks passed.
- Unit assertions cover filtered question numbering, review exclusion, correct/incorrect/skipped counts, negative scores, exact multiple answers, numeric ranges, 100% readiness and no-scorable-question reports.
- Local 2025 Advanced Paper 1: 33 scored questions from 48 source positions; correct MCQ + incorrect partial multiple answer + correct numeric answer = 7/132. Answers/timer survived reload. Full-paper mode independently retained 48 questions; expiry submitted automatically, and a response to a review-only question did not change the score.
- Local IIT-JEE 2005: all 22 questions remain pending. Scored mode refuses an empty test; full-paper submission produces “Not graded” and “Not available” readiness.
- Print / Save PDF route reached the browser print function with the complete 33-question report and all images loaded. The actual OS PDF-save interaction was not automated.
- Live Advanced Paper 1: 33-question submission, verified 7/132 in desktop interaction and 4/132 for a single correct response on mobile. At 390px viewport, document width is 390px, answers stack below questions and answer text is 26.4px.
- Live Advanced report downloaded successfully: 1,697,029 bytes, 33 question reviews, 16 embedded and rendered images (including the logo), 9,949 formula references, no unresolved glyph references and no competitor brand strings. Rendered in a document that blocks external resources.
- Live JEE Main mixed mock 69: 75 questions, including a diagram from the separate reviewed-image prefix. Download passed: 1,525,073 bytes, every image embedded and rendered, 8,897 formula references, zero unresolved glyph references, no scripts and no competitor brand strings. Also visually inspected the downloaded report rendering.
- Bounded live regression suite passed 35 checks: question pages, all 16 recent approved Advanced diagram digests, and three concurrent complete PDF downloads with matching hashes.
- Removed the temporary deployment SSH allowance; retained the original firewall entry.

## Content still pending

Advanced recovery remains at 1,814 scorable out of 3,962 distinct questions. The other 2,148 comprise 1,407 needing a usable key, 469 needing a prompt/option diagram, 266 needing both and six key conflicts. Solution illustrations are separately pending for 1,051 questions, including 368 otherwise scorable. No answer was inferred to suppress a warning. Only the existing approved images are used.
