# Phase 1 — GeeksforGeeks interface reconstruction

## Goal
Build a navigable, frontend-only reconstruction of the observable GeeksforGeeks page system. Preserve its dense editorial character, route families, responsive navigation, catalog controls, and representative interaction states while keeping all content replaceable.

## Build scope
- Create the shared site frame: desktop and mobile headers, search, account controls, topic strip, mega menu, breadcrumbs, subject navigation, footer, dialogs, loading/error/empty/access-required states.
- Establish semantic visual tokens for the reference palette, typography, compact spacing, borders, controls, cards, code blocks, tables, and accessible focus states.
- Add data-driven fixtures and route records for subjects, topics, articles, interviews, projects, problems, quizzes, courses, videos, events, contests, companies, jobs, authors, and utility pages.
- Implement distinct templates for:
  - Home, directories, hubs, archives, search, pagination
  - Subject curricula, concept/algorithm/comparison/interview/reference/project articles
  - Practice catalog, problem workspace, POTD/archive, quizzes, guided learning
  - Course catalog/category/detail, checkout, learner dashboard/workspace/progress
  - Video catalog/detail, events, campaigns, contests, leaderboards
  - Jobs, companies, applications, corporate/recruiter/advertising/campus pages
  - Sign-in/recovery, profile/settings/bookmarks/notifications, about/contact/legal/help
- Wire every visible navigation control to a valid local destination; preserve query-driven filtering, sorting, tab, and pagination state.
- Provide a catch-all resolver for reference-style content paths without allowing it to swallow priority application routes; unknown paths receive a designed 404.
- Add a development-only coverage page with route-family status, populated samples, inferred/private labels, and inventory limitations.

## Interaction and accessibility
- Functional keyboard-operable menus, dialogs, accordions, tabs, filters, pagination, editor controls, form validation, and mobile navigation.
- Frontend-only actions clearly identify demo, sign-in-required, or unavailable states; no simulated successful judging, payment, enrollment, or submission.
- Responsive layouts checked at 1440px desktop and 390px mobile, with contained horizontal scrolling for code/tables and no page-wide overflow.

## Verification
- Compare representative public page families against live references where accessible and document blocked or inferred screens.
- Exercise direct navigation, refresh, Back/Forward, query state, filters, pagination, empty states, forms, and missing routes.
- Check internal links, runtime/console errors, metadata, mobile/desktop rendering, and the current build signal.
- Report exact implemented family/sample counts, imported/resolved/unresolved URL counts, visually compared pages, inferred screens, remaining discrepancies, and deferred backend work.

## Technical details
- Keep TanStack Start file routes for priority application pages and a data-driven catch-all for content families.
- Keep large URL inventory data outside the initial browser bundle. The uploaded brief contains no frozen URL inventory, so implement the importer/resolver structure and use representative routes discovered from the prompt/current sitemap; report complete-snapshot import as outstanding unless the sitemap can be acquired reliably during this phase.
- Use local fixtures only. No authentication, database, payment, email, judging, video delivery, or external submissions are added in Phase 1.
