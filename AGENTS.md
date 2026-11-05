<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

## Project architecture

- For all Dekhoexams education work, follow `SITE-ARCHITECTURE.md` and keep `IMPLEMENTATION-STATUS.md` honest. Preserve the current Dekhoexams shell and typography. The user-approved October 1 refresh uses six saturated-color shortcuts and an 18-group subject directory; keep this design unless explicitly asked to redesign.
- `src/lib/education-catalog.ts` is the source of truth for education route ownership, canonical URLs, aliases, navigation, breadcrumbs and indexability. Never create guessed combinations or independent duplicate lesson records for each board or language.
- Canonical public origin is `https://pencil2pen.com`; the brand is Dekhoexams. Old `/study` URLs permanently redirect. Internal links must use current canonical routes.
- Preserve stable resource IDs when moving URLs; preserve old question versions when changing answer semantics. Add aliases only for equivalent moved resources. Unknown owned paths must return 404 rather than falling through to CMS fixtures.
- No NCERT/board alignment, translated content, reviewer identity, download licence, full mock test, learner count or traffic claim without evidence. Unfilled collections and unreviewed resources remain noindex and absent from sitemaps, even in a non-preview build.
- Run `npm run test:education`, production build, TypeScript and relevant HTTP/UI checks for route changes. The build automatically checks catalog invariants. The CMS integration below is legacy, not an implemented school publishing workflow.

- Keep reusable page templates in `src/components/cms`; one published WordPress entry maps to one URL through the TanStack catch-all route.
- Use Dekhoexams branding for the public interface. Legacy AITrove CMS/API and content assets are migration details, not public branding.
- The inherited WordPress integration owns computing-library editorial login, drafts, and publishing; review it before using it for Dekhoexams school content.
- For verified site changes, commit on `main`, merge newer `origin/main` without force-pushing or discarding remote work, push to `sunandgarg/lovable-2025-standard`, deploy the existing `pencil2pen-frontend` Worker, and check the changed route at `https://pencil2pen.com`. Keep preview `noindex` until the user explicitly approves an indexed launch. Do not deploy to the inherited AITrove project.
- Keep sample fixtures for local preview. Do not use the former Lovable Cloud database or first-admin signup flow.
- Gated, judged, paid, submitted, or authenticated features need real backend services before being presented as functional.

- Courses are archived behind `FEATURES.courses` in `src/lib/features.ts` (currently false). Preserve their code/content; do not restore public links, search results or routes unless the user asks to launch courses.

## AI Trove editorial rules

- New tutorials use original semantic HTML: p, h2, h3, ul, li, strong, pre/code with language classes, and a for deliberate internal lesson links. No Markdown, tables, columns, or grids in tutorial bodies. Keep source links out of new public tutorial bodies.
- Start with the technical definition. Write directly for developers, with practical examples, performance costs, failure cases, and a Common Mistakes or Edge Cases h3. Avoid generic foo/bar or Animal/Dog examples, marketing praise, filler introductions, and line-by-line narration.
- Avoid: delve, leverage, harness, foster, streamline, showcase, navigate, demystify, furthermore, moreover, additionally, robust, crucial, pivotal, multifaceted, bespoke, seamless, dynamic, quintessential, nuanced, powerful, versatile. Vary sentence length naturally and stop when the technical explanation is finished.
- Do not describe generated writing as human-authored or guarantee outcomes from AI-detection tools.

- Research may verify technical facts against official documentation. Write fresh explanations, programs, exercises, and diagrams; changing identifiers or values in a copied example is not an originality workflow. Keep research URLs in the editorial handoff, not in public tutorial bodies. Internal lesson links must resolve to published routes.
- Do not promise exclusive ownership of Java facts, API syntax, third-party logos, or open-source dependencies. Preserve required third-party licences.
- Question bank data lives in `src/lib/question-bank.ts` (stable question IDs and versions); keep `year`/`shift` null unless the question comes from a verified, rights-cleared past paper. Why: practice questions must never pass as past papers.

- Tailwind must not scan `src/data` (`@source not "./data"` in styles.css): its multi-MB fixtures stall the dev server CSS transform.
- Exam groups, exams, units and papers live in `src/lib/question-bank.ts`; papers are `kind: "practice"` with null year until a verified past paper is added.
