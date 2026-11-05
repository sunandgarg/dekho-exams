import { PrivacyControls } from "@/components/cms/privacy-controls";
import { Link, useRouterState } from "@tanstack/react-router";
import {
  Bookmark,
  BookOpen,
  GraduationCap,
  Home,
  Menu,
  Moon,
  PencilLine,
  Search,
  Sun,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { EDUCATION_NAV as NAV_GROUPS, educationPage } from "@/lib/education-catalog";

export function LocalLink({
  href,
  className,
  children,
  ...rest
}: {
  href: string;
  className?: string;
  children: ReactNode;
  "aria-label"?: string;
}) {
  const clean = href.replace(/^\/+|\/+$/g, "");
  if (clean === "study")
    return (
      <Link to="/study" className={className} {...rest}>
        {children}
      </Link>
    );
  if (clean.startsWith("study/"))
    return (
      <a href={`/${clean}`} className={className} {...rest}>
        {children}
      </a>
    );
  if (clean === "about" || clean === "privacy")
    return (
      <a href={`/${clean}`} className={className} {...rest}>
        {children}
      </a>
    );
  return clean ? (
    <Link
      to="/$"
      params={{ _splat: clean }}
      activeOptions={{ exact: true }}
      className={className}
      {...rest}
    >
      {children}
    </Link>
  ) : (
    <Link to="/" activeOptions={{ exact: true }} className={className} {...rest}>
      {children}
    </Link>
  );
}
export function SiteShell({ children }: { children: ReactNode }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const home = pathname === "/";
  const educationRoute = educationPage(pathname);
  const learning = !!educationRoute && educationRoute.family !== "utility";
  const [searchOpen, setSearchOpen] = useState(false);
  const [dark, setDark] = useState(false);
  const [themeReady, setThemeReady] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  useEffect(() => {
    try {
      setDark(localStorage.getItem("penpencil-theme") === "dark");
    } catch {
      /* Storage is optional. */
    }
    setThemeReady(true);
  }, []);
  useEffect(() => {
    if (!themeReady) return;
    document.documentElement.classList.toggle("dark", dark);
    try {
      localStorage.setItem("penpencil-theme", dark ? "dark" : "light");
    } catch {
      /* The visual theme still works. */
    }
  }, [dark, themeReady]);
  useEffect(() => {
    setMobileOpen(false);
    setSearchOpen(false);
    const header = document.querySelector<HTMLElement>("[data-site-header]");
    if (!header) return;
    const measure = () => {
      document.documentElement.style.setProperty(
        "--site-header-height",
        `${header.getBoundingClientRect().height}px`,
      );
      const topics = header.querySelector<HTMLElement>(".ozi-topic-nav");
      const active = topics?.querySelector<HTMLElement>('a[aria-current="page"]');
      if (topics && active) {
        const bounds = topics.getBoundingClientRect();
        const item = active.getBoundingClientRect();
        if (item.left < bounds.left || item.right > bounds.right)
          topics.scrollLeft += item.left - bounds.left - (topics.clientWidth - item.width) / 2;
      }
    };
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(header);
    return () => observer.disconnect();
  }, [pathname]);
  if (pathname.startsWith("/admin"))
    return <div className="min-h-screen bg-background text-foreground">{children}</div>;
  const libraryTopics = [
    ["Classes 1–12", "classes"],
    ["Question Bank", "questions"],
    ["NCERT", "ncert"],
    ["CBSE", "cbse"],
    ["CISCE", "cisce"],
    ["Class 10", "class-10"],
    ["Class 12", "class-12"],
    ["JEE", "jee"],
    ["NEET", "neet"],
    ["CUET", "cuet"],
    ["State Books", "state-boards"],
    ["Languages", "languages"],
    ["All subjects", "subjects"],
  ];
  return (
    <div
      className="ozi-site min-h-screen bg-background text-foreground"
      data-app-ready={themeReady ? "true" : "false"}
      data-homepage={home ? "true" : undefined}
      data-learning-page={learning ? "true" : undefined}
    >
      <NavigationProgress booting={!themeReady} />
      <a
        href="#main-content"
        className="sr-only fixed left-3 top-3 z-50 rounded bg-primary px-4 py-2 text-primary-foreground focus:not-sr-only"
      >
        Skip to content
      </a>
      <header data-site-header className={`ozi-header ${home ? "ozi-header-home" : ""}`}>
        <div className="ozi-header-top">
          <Link to="/" className="ozi-brand-link">
            <Brand />
            <span className="brand-caption">Learn. Practice. Grow.</span>
          </Link>
          <form
            action="/search"
            role="search"
            aria-label="Site search"
            className={`ozi-search ${home || searchOpen ? "search-mobile-open" : ""}`}
          >
            <Search aria-hidden="true" className="size-5" />
            <label className="sr-only" htmlFor="global-search">
              Search resources
            </label>
            <Input id="global-search" name="q" placeholder="Search lessons and subjects…" />
            <button type="submit">
              Search <span aria-hidden="true">→</span>
            </button>
          </form>
          <div className="ozi-header-actions">
            <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" className="browse-trigger" aria-label="Open navigation">
                  <Menu className="size-5" />
                  <span>Browse</span>
                </Button>
              </SheetTrigger>
              <SheetContent
                side="left"
                className="ozi-navigation-drawer w-[90%] max-w-sm overflow-y-auto p-0"
              >
                <SheetHeader className="border-b p-6 text-left">
                  <SheetTitle>Browse the library</SheetTitle>
                  <p className="text-sm text-muted-foreground">
                    Find a subject, a problem, or your next read.
                  </p>
                </SheetHeader>
                <nav
                  className="p-4"
                  onClick={(e) => {
                    if ((e.target as HTMLElement).closest("a")) setMobileOpen(false);
                  }}
                >
                  {NAV_GROUPS.map((group) => (
                    <details key={group.label} className="border-b">
                      <summary className="cursor-pointer py-4 text-sm font-bold">
                        {group.label}
                      </summary>
                      <div className="pb-4">
                        {group.sections.map((section) => (
                          <div key={section.title} className="mt-3">
                            <p className="px-3 text-xs font-bold uppercase tracking-wider text-muted-foreground">
                              {section.title}
                            </p>
                            {section.links.map(([label, path]) => (
                              <LocalLink
                                key={path}
                                href={path!}
                                className="block rounded-lg px-3 py-3 text-sm hover:bg-accent"
                              >
                                {label}
                              </LocalLink>
                            ))}
                          </div>
                        ))}
                      </div>
                    </details>
                  ))}
                  <LocalLink href="my-study" className="block py-4 text-sm font-bold">
                    Your saved reading
                  </LocalLink>
                  <a href="/questions" className="block py-3 text-sm font-bold">
                    Question Bank
                  </a>
                  <a href="/about" className="block py-3 text-sm font-bold">
                    About Pencil2Pen
                  </a>
                </nav>
              </SheetContent>
            </Sheet>
            {!home && (
              <Button
                variant="ghost"
                size="icon"
                className="ozi-mobile-search"
                aria-label="Search"
                onClick={() => setSearchOpen(!searchOpen)}
              >
                <Search />
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon"
              aria-label="Toggle theme"
              onClick={() => setDark(!dark)}
            >
              {dark ? <Sun /> : <Moon />}
            </Button>
            <LocalLink href="my-study" className="ozi-saved-link" aria-label="Your reading list">
              <Bookmark className="size-5" />
              <span>Reading list</span>
            </LocalLink>
          </div>
        </div>
        <nav aria-label="Popular topics" className="ozi-topic-nav">
          <div>
            {libraryTopics.map(([label, path], index) => (
              <LocalLink
                key={path}
                href={path!}
                className={`ozi-topic-link category-${index % 5}`}
                aria-current={
                  pathname === "/" + path ||
                  pathname.startsWith(`/${path}/`) ||
                  (path === "classes" && /^\/class-\d+/.test(pathname))
                    ? "page"
                    : undefined
                }
              >
                <span className="ozi-topic-image">
                  {label === "All subjects" ? (
                    <BookOpen className="size-6" />
                  ) : path!.startsWith("class") ? (
                    <GraduationCap className="size-6" />
                  ) : (
                    <BookOpen className="size-6" />
                  )}
                </span>
                <span>{label}</span>
              </LocalLink>
            ))}
          </div>
        </nav>
      </header>
      <main id="main-content" tabIndex={-1} className={home ? undefined : "editorial-page"}>
        {children}
      </main>
      <Footer />
      <PrivacyControls />
      <nav aria-label="Mobile navigation" className="ozi-bottom-nav">
        {[
          ["Home", "", Home],
          ["Classes", "classes", GraduationCap],
          ["Exams", "exams", BookOpen],
          ["Saved", "my-study", Bookmark],
        ].map(([label, path, Icon]) => {
          const href = String(path);
          const Symbol = Icon as typeof Home;
          return (
            <LocalLink
              key={href}
              href={href}
              aria-current={pathname === (href ? "/" + href : "/") ? "page" : undefined}
            >
              <Symbol className="size-5" aria-hidden="true" />
              <span>{String(label)}</span>
            </LocalLink>
          );
        })}
      </nav>
    </div>
  );
}

function NavigationProgress({ booting }: { booting: boolean }) {
  const loading = useRouterState({ select: (state) => state.isLoading });
  const pending = booting || loading;
  const [visible, setVisible] = useState(booting);

  useEffect(() => {
    const timer = window.setTimeout(() => setVisible(pending), pending ? (booting ? 0 : 140) : 300);
    return () => window.clearTimeout(timer);
  }, [pending, booting]);

  if (!visible) return null;

  return (
    <div
      className="trove-page-progress"
      data-complete={!pending}
      role="status"
      aria-label="Loading page"
    >
      <span className="trove-page-progress-fill">
        <PencilLine aria-hidden="true" width={22} height={22} />
      </span>
    </div>
  );
}

function Brand() {
  return (
    <span className="trove-brand">
      <span className="trove-brand-wordmark">
        pencil<span className="pencil2pen-digit">2</span>pen
      </span>
    </span>
  );
}
function Footer() {
  return (
    <footer className="ozi-footer border-t bg-footer text-footer-foreground">
      <div className="mx-auto max-w-[1320px] px-5 py-12">
        <div className="mb-10 flex flex-wrap items-start justify-between gap-6">
          <div>
            <Brand />
            <p className="mt-3 max-w-md text-sm leading-6 text-footer-muted">
              Classes 1–12, books, boards and entrance exam directories. Original lessons with
              worked examples and practice.
            </p>
          </div>
          <div className="grid gap-3 text-sm">
            <a href="/classes" className="font-bold">
              Explore all classes →
            </a>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-8 sm:grid-cols-3 lg:grid-cols-4">
          {[
            {
              title: "Pencil2Pen",
              links: [
                ["About", "about"],
                ["Privacy", "privacy"],
                ["All collections", "site-map"],
              ],
            },
            ...NAV_GROUPS.map((g) => ({
              title: g.label,
              links: g.sections.flatMap((s) => [...s.links]),
            })),
          ].map((g) => (
            <section key={g.title}>
              <h2 className="text-sm font-bold">{g.title}</h2>
              <div className="mt-4 grid gap-3">
                {g.links.map(([label, path]) => (
                  <LocalLink
                    key={path}
                    href={path!}
                    className="text-xs leading-5 text-footer-muted hover:text-footer-foreground"
                  >
                    {label}
                  </LocalLink>
                ))}
              </div>
            </section>
          ))}
        </div>
      </div>
      <div className="border-t border-footer-border px-5 py-4 text-center text-xs text-footer-muted">
        © 2026 Pencil2Pen
      </div>
    </footer>
  );
}
