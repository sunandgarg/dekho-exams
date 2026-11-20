import { useState, useEffect, type ReactNode } from "react";
import {
  ArrowUpRight,
  BookOpen,
  Check,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Download,
  FileText,
  Gift,
  GraduationCap,
  LayoutDashboard,
  LockKeyhole,
  Plus,
  ShieldCheck,
  Ticket,
  Users,
  X,
} from "lucide-react";
import {
  MONTHLY_PRICE_PAISE,
  STUDENT_OFFERS,
  quoteAccess,
  type Coupon,
} from "@/lib/student-offers";
import * as Dialog from "@radix-ui/react-dialog";
import { PreviewBreakdown, PreviewDiagnostic, PreviewQuestionReview } from "./preview-diagnostic";
import { blankPreviewAnswers, previewQuestions, previewResult } from "./preview-diagnostic-data";
import "./platform-preview.css";

type View = "home" | "join" | "checkout" | "test" | "report" | "admin";
type Profile = {
  contact: { name: string; email: string; mobile: string } | null;
  education: { level: string; state: string; city: string } | null;
  preferences: { dob: string } | null;
};
const initialProfile: Profile = { contact: null, education: null, preferences: null };
const money = (paise: number) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(paise / 100);
const states = [
  "Andhra Pradesh",
  "Arunachal Pradesh",
  "Assam",
  "Bihar",
  "Chhattisgarh",
  "Goa",
  "Gujarat",
  "Haryana",
  "Himachal Pradesh",
  "Jharkhand",
  "Karnataka",
  "Kerala",
  "Madhya Pradesh",
  "Maharashtra",
  "Manipur",
  "Meghalaya",
  "Mizoram",
  "Nagaland",
  "Odisha",
  "Punjab",
  "Rajasthan",
  "Sikkim",
  "Tamil Nadu",
  "Telangana",
  "Tripura",
  "Uttar Pradesh",
  "Uttarakhand",
  "West Bengal",
  "Andaman and Nicobar Islands",
  "Chandigarh",
  "Dadra and Nagar Haveli and Daman and Diu",
  "Delhi",
  "Jammu and Kashmir",
  "Ladakh",
  "Lakshadweep",
  "Puducherry",
];

function Action({
  children,
  onClick,
  secondary = false,
  disabled = false,
  type = "button",
}: {
  children: ReactNode;
  onClick?: () => void;
  secondary?: boolean;
  disabled?: boolean;
  type?: "button" | "submit";
}) {
  return (
    <button
      type={type}
      className={secondary ? "sp-button sp-secondary" : "sp-button"}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
}
function Title({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children?: ReactNode;
}) {
  return (
    <div className="sp-title">
      <p className="sp-eyebrow">{eyebrow}</p>
      <h1 tabIndex={-1}>{title}</h1>
      {children && <p className="sp-description">{children}</p>}
    </div>
  );
}
function Metric({
  label,
  value,
  detail,
  tone = "blue",
}: {
  label: string;
  value: string;
  detail: string;
  tone?: string;
}) {
  return (
    <div className={"sp-metric sp-" + tone}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}

export function PlatformPreview() {
  const [view, setView] = useState<View>("home");
  const [profile, save] = useState<Profile>(initialProfile);
  const [card, showCard] = useState<"login" | "contact" | "education" | "birthday">("login");
  const [loginMethod, method] = useState("google");
  const [otp, setOtp] = useState(false);
  const [couponsOpen, openCoupons] = useState(false);
  const [coupon, selectCoupon] = useState<string | null>(null);
  const [couponInput, enterCoupon] = useState("");
  const [notice, notify] = useState("");
  const [answers, setAnswers] = useState<string[] | null>(null);
  const [flags, setFlags] = useState<boolean[]>([]);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [report, setReport] = useState<ReturnType<typeof previewResult> | null>(null);
  const submitted = report !== null;
  const [welcomeUsed, useWelcome] = useState(false);
  const [comebackUsed, useComeback] = useState(false);
  const [schoolUsed, useSchool] = useState(false);
  const [schoolIssued, issueSchool] = useState(false);
  const [schoolName, nameSchool] = useState("Your partner school");
  const [schoolForm, showSchoolForm] = useState(false);
  const [studentDetail, showStudent] = useState(false);
  const go = (next: View) => {
    setView(next);
    notify("");
    window.scrollTo({ top: 0, behavior: "instant" });
  };
  useEffect(() => {
    if (view === "join") document.querySelector<HTMLElement>(".sp-form-card h2")?.focus();
    if (view === "report") document.querySelector<HTMLElement>(".sp-title h1")?.focus();
  }, [view, card]);
  const ready = !!profile.contact && !!profile.education;
  const openDiagnostic = () => {
    if (!answers) {
      setAnswers(blankPreviewAnswers());
      setFlags([]);
      setQuestionIndex(0);
    }
    go("test");
  };
  const book = () => {
    if (!ready) {
      showCard(profile.contact ? "education" : "login");
      go("join");
    } else go("checkout");
  };
  const offer = coupon
    ? ({
        id: coupon,
        kind:
          coupon === "WELCOME100" ? "welcome" : coupon === "COMEBACK100" ? "comeback" : "school",
        exam: "jee-main",
        active: true,
        startsAt: 0,
        expiresAt: 8e15,
        limit: 1000,
        used: 0,
      } as Coupon)
    : null;
  const used =
    coupon === "WELCOME100"
      ? welcomeUsed
      : coupon === "COMEBACK100"
        ? comebackUsed
        : coupon === "SCHOOL-DEMO" && schoolUsed;
  let due = MONTHLY_PRICE_PAISE,
    offerError = "";
  try {
    due = quoteAccess(
      {
        verified: true,
        profileReady: true,
        consentReady: true,
        submittedAttempts: submitted ? 1 : 0,
      },
      "jee-main",
      offer,
      used,
    ).duePaise;
  } catch (e) {
    offerError = (e as Error).message;
  }
  const apply = (code: string) => {
    const normalized = code.trim().toUpperCase();
    if (!["WELCOME100", "COMEBACK100", "SCHOOL-DEMO"].includes(normalized)) {
      notify("For this design preview, try WELCOME100 or SCHOOL-DEMO.");
      return;
    }
    if (
      (normalized === "WELCOME100" && (submitted || welcomeUsed)) ||
      (normalized === "COMEBACK100" && (!submitted || comebackUsed)) ||
      (normalized === "SCHOOL-DEMO" && schoolUsed)
    ) {
      notify("This offer isn't eligible right now. Check its details below.");
      return;
    }
    selectCoupon(normalized);
    openCoupons(false);
    notify("");
  };
  const startTest = () => {
    if (due || offerError) {
      notify(
        "Apply a sample coupon to preview the free checkout, or open the diagnostic from your dashboard.",
      );
      return;
    }
    if (answers) {
      go("test");
      return;
    }
    if (coupon === "WELCOME100") useWelcome(true);
    if (coupon === "COMEBACK100") useComeback(true);
    if (coupon === "SCHOOL-DEMO") useSchool(true);
    openDiagnostic();
  };
  const finish = () => {
    if (!answers) return;
    setReport(previewResult(answers));
    setAnswers(null);
    selectCoupon(null);
    go("report");
  };
  const name = profile.contact?.name.split(" ")[0] || "there";
  return (
    <div className="student-preview">
      <div className="sp-preview-note">
        <span>
          <span className="sp-preview-dot" /> Interactive design preview
        </span>
        <span>Sample journey · no sign-in, payment or personal data is sent</span>
      </div>
      <header className="sp-header">
        <a href="/" aria-label="DekhoExams home">
          <img src="/logos/dekhoexams-wordmark.png" alt="DekhoExams" width="178" height="36" />
        </a>
        <nav aria-label="Design views">
          <button aria-current={view !== "admin" ? "page" : undefined} onClick={() => go("home")}>
            Student
          </button>
          <button aria-current={view === "admin" ? "page" : undefined} onClick={() => go("admin")}>
            Admin & schools
          </button>
        </nav>
        <button
          className="sp-avatar"
          aria-label="Preview student profile"
          onClick={() => {
            showCard("login");
            go("join");
          }}
        >
          {profile.contact?.name[0]?.toUpperCase() || "You"}
        </button>
      </header>
      <div className="sp-layout">
        <aside className="sp-sidebar">
          <p className="sp-sidebar-label">
            {view === "admin" ? "PARTNER DESK" : "YOUR STUDY SPACE"}
          </p>
          {(view === "admin"
            ? [
                { label: "Overview", icon: LayoutDashboard, next: "admin" },
                { label: "School coupons", icon: Ticket, next: "admin" },
                { label: "Students", icon: Users, next: "admin" },
              ]
            : [
                { label: "My space", icon: LayoutDashboard, next: "home" },
                { label: "Mock tests", icon: BookOpen, next: "checkout" },
                { label: "My reports", icon: FileText, next: "report" },
                { label: "My profile", icon: GraduationCap, next: "join" },
              ]
          ).map(({ label, icon: Icon, next }) => (
            <button
              key={label}
              className={view === next ? "sp-nav-active" : ""}
              onClick={() => {
                if (next === "checkout") book();
                else if (next === "join") {
                  showCard(profile.contact ? "education" : "login");
                  go("join");
                } else if (next === "report" && !submitted)
                  notify("Complete the diagnostic to view your report.");
                else go(next as View);
                if (label === "School coupons") showSchoolForm(true);
                if (label === "Students") showStudent(true);
              }}
            >
              <Icon size={19} />
              {label}
            </button>
          ))}
          <div className="sp-aside-tip">
            <Gift size={22} />
            <strong>A little head start.</strong>
            <p>Your first mock is free with WELCOME100.</p>
            <button onClick={book}>
              See my offers <ChevronRight size={16} />
            </button>
          </div>
          <div className="sp-side-bottom">
            <ShieldCheck size={17} /> Your progress. Your space.
          </div>
        </aside>
        <main className="sp-main" id="student-preview-main">
          {notice && (
            <div role="status" className="sp-notice">
              {notice}
              <button aria-label="Dismiss message" onClick={() => notify("")}>
                <X size={17} />
              </button>
            </div>
          )}
          {view === "home" && (
            <>
              <section className="sp-hero sp-practice-hero">
                <div>
                  <p className="sp-eyebrow">DEKHOEXAMS PRACTICE</p>
                  <h1>
                    {name === "there"
                      ? "Make your next mock count."
                      : `${name}, ready for your next mock?`}
                  </h1>
                  <p>Take a short JEE Main diagnostic and see which chapter to practise next.</p>
                  <div className="sp-hero-actions">
                    <Action onClick={openDiagnostic}>
                      {answers ? "Resume diagnostic" : "Try the free diagnostic"}{" "}
                      <ArrowUpRight size={18} />
                    </Action>
                    {report && (
                      <Action secondary onClick={() => go("report")}>
                        Open latest report
                      </Action>
                    )}
                  </div>
                  <p className="sp-hero-detail">
                    6 original questions · Physics, Chemistry and Mathematics
                  </p>
                </div>
                <div className="sp-test-ticket">
                  <p className="sp-eyebrow">MONTHLY PASS PREVIEW</p>
                  <h2>
                    <strong>{money(MONTHLY_PRICE_PAISE)}</strong>
                    <small> / month</small>
                  </h2>
                  <p>Unlimited mocks for one calendar month.</p>
                  <ul>
                    <li>
                      <Check size={16} />
                      Full mock library
                    </li>
                    <li>
                      <Check size={16} />
                      Subject breakdowns and practice recommendations
                    </li>
                    <li>
                      <Ticket size={16} />A coupon covers one mock
                    </li>
                  </ul>
                  <button type="button" className="sp-button sp-secondary" onClick={book}>
                    Preview checkout <ChevronRight size={17} />
                  </button>
                </div>
              </section>
              <div className="sp-section-heading">
                <h2>Find a practice session</h2>
              </div>
              <div className="sp-three sp-practice-catalog">
                <article className="sp-info-card">
                  <span className="sp-icon sp-blue">
                    <GraduationCap size={22} />
                  </span>
                  <h3>JEE Main</h3>
                  <p>
                    Choose a previous-year paper or a mixed practice test. Check your score, pace
                    and accuracy.
                  </p>
                  <a href="/questions/jee-main/mock-tests">
                    Browse Main mocks <ChevronRight size={16} />
                  </a>
                </article>
                <article className="sp-info-card">
                  <span className="sp-icon sp-purple">
                    <BookOpen size={22} />
                  </span>
                  <h3>JEE Advanced</h3>
                  <p>
                    Work through timed papers and mixed question sets. Review your answers after
                    submission.
                  </p>
                  <a href="/questions/jee-advanced/mock-tests">
                    Browse Advanced mocks <ChevronRight size={16} />
                  </a>
                </article>
                <article className="sp-info-card">
                  <span className="sp-icon sp-orange">
                    <Ticket size={22} />
                  </span>
                  <h3>School pilot</h3>
                  <p>
                    Use the access link from your school to open your diagnostic, report and earned
                    awards.
                  </p>
                  <a href="/platform-student">
                    Join as a student <ChevronRight size={16} />
                  </a>
                  <a className="sp-school-panel-link" href="/platform-school">
                    Open school panel <ChevronRight size={16} />
                  </a>
                </article>
              </div>
              <div className="sp-bottom-note">
                <BookOpen size={18} />
                <p>Pick a chapter for a focused revision session.</p>
                <a href="/past-years/jee/jee-main">
                  Browse chapter questions <ArrowUpRight size={16} />
                </a>
              </div>
            </>
          )}
          {view === "join" && (
            <div className="sp-onboarding">
              <div className="sp-onboarding-copy">
                <span className="sp-tiny-pill">MADE FOR YOUR NEXT STEP</span>
                <h2>
                  A study space
                  <br />
                  that feels like yours.
                </h2>
                <p>
                  A few useful details help us keep the right tests and reports together for you.
                </p>
                <div className="sp-small-benefit">
                  <CheckCircle2 /> Your progress across devices
                </div>
                <div className="sp-small-benefit">
                  <CheckCircle2 /> Two free mock offers
                </div>
                <div className="sp-small-benefit">
                  <CheckCircle2 /> Your reports, easy to find
                </div>
                <p className="sp-preview-footnote">
                  This is a design walkthrough. Use sample details only. Values stay in memory and
                  disappear when this page reloads. The live flow will include age eligibility and
                  guardian consent.
                </p>
              </div>
              <section className="sp-form-card" aria-label="Profile preview">
                {card === "login" && (
                  <>
                    <span className="sp-icon sp-blue">
                      <GraduationCap />
                    </span>
                    <h2 tabIndex={-1}>Good to have you here.</h2>
                    <p>Choose how you'd like to sign in.</p>
                    <Action
                      secondary
                      onClick={() => {
                        method("google");
                        showCard("contact");
                      }}
                    >
                      <span className="sp-google">G</span> Preview Google sign-in
                    </Action>
                    <div className="sp-or">
                      <span />
                      or use your mobile
                      <span />
                    </div>
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        method("phone");
                        setOtp(true);
                      }}
                    >
                      <Field
                        label="Mobile number"
                        type="tel"
                        name="mobile"
                        autoComplete="tel"
                        placeholder="+91 mobile number"
                        required
                        pattern="(?:\+91)?[6-9][0-9]{9}"
                        defaultValue="9876500000"
                      />
                      {!otp && <Action type="submit">Preview OTP screen</Action>}
                    </form>
                    {otp && (
                      <form
                        onSubmit={(e) => {
                          e.preventDefault();
                          showCard("contact");
                        }}
                      >
                        <Field
                          label="Enter the preview code"
                          name="otp"
                          inputMode="numeric"
                          autoComplete="one-time-code"
                          pattern="[0-9]{6}"
                          maxLength={6}
                          placeholder="Any six digits in this preview"
                          required
                        />
                        <p className="sp-muted">
                          No SMS is sent. A live code will expire and have retry limits.
                        </p>
                        <Action type="submit">Continue preview</Action>
                      </form>
                    )}
                    <p className="sp-form-footer">
                      Your details will be used for your account and test reports.{" "}
                      <a href="/privacy">Privacy policy</a>
                    </p>
                  </>
                )}
                {card === "contact" && (
                  <>
                    <span className="sp-icon sp-blue">
                      <Users />
                    </span>
                    <h2 tabIndex={-1}>What should we call you?</h2>
                    <p>Let's keep your test reports in the right place.</p>
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        const f = new FormData(e.currentTarget);
                        save((p) => ({
                          ...p,
                          contact: {
                            name: String(f.get("name")),
                            email: String(f.get("email")),
                            mobile: String(f.get("mobile")),
                          },
                        }));
                        showCard("education");
                        notify("Contact details saved in preview memory.");
                      }}
                    >
                      <Field
                        label="Full name"
                        name="name"
                        autoComplete="name"
                        maxLength={120}
                        required
                        defaultValue={profile.contact?.name || "Riya Sharma"}
                      />
                      <Field
                        label="Email"
                        name="email"
                        type="email"
                        autoComplete="email"
                        maxLength={254}
                        required
                        defaultValue={profile.contact?.email || "riya@example.com"}
                      />
                      <Field
                        label="Mobile"
                        name="mobile"
                        type="tel"
                        autoComplete="tel"
                        pattern="(?:\+91)?[6-9][0-9]{9}"
                        required
                        defaultValue={profile.contact?.mobile || "9876500000"}
                      />
                      <p className="sp-muted">
                        In the live flow,{" "}
                        {loginMethod === "google"
                          ? "Google confirms your email; a mobile code verifies your number."
                          : "OTP confirms your phone; email verification stays separate."}
                      </p>
                      <Action type="submit">Save and continue</Action>
                    </form>
                  </>
                )}
                {card === "education" && (
                  <>
                    <span className="sp-icon sp-orange">
                      <GraduationCap />
                    </span>
                    <h2 tabIndex={-1}>Where are you learning?</h2>
                    <p>We'll help you find practice that fits.</p>
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        const f = new FormData(e.currentTarget);
                        save((p) => ({
                          ...p,
                          education: {
                            level: String(f.get("level")),
                            state: String(f.get("state")),
                            city: String(f.get("city")),
                          },
                        }));
                        showCard("birthday");
                        notify("Education and location saved separately in preview memory.");
                      }}
                    >
                      <label className="sp-field">
                        Currently studying
                        <select
                          name="level"
                          defaultValue={profile.education?.level || "12"}
                          required
                        >
                          <option value="10">Class 10</option>
                          <option value="11">Class 11</option>
                          <option value="12">Class 12</option>
                          <option value="graduation">Graduation</option>
                          <option value="masters">Masters</option>
                        </select>
                      </label>
                      <label className="sp-field">
                        State / Union territory
                        <select
                          name="state"
                          defaultValue={profile.education?.state || "Delhi"}
                          required
                        >
                          {states.map((s) => (
                            <option key={s}>{s}</option>
                          ))}
                        </select>
                      </label>
                      <Field
                        label="City"
                        name="city"
                        autoComplete="address-level2"
                        required
                        maxLength={100}
                        defaultValue={profile.education?.city || "New Delhi"}
                      />
                      <Action type="submit">Save and continue</Action>
                      <button
                        type="button"
                        className="sp-text-button"
                        onClick={() => showCard("contact")}
                      >
                        Back to contact details
                      </button>
                    </form>
                  </>
                )}
                {card === "birthday" && (
                  <>
                    <span className="sp-icon sp-green">
                      <Gift />
                    </span>
                    <h2 tabIndex={-1}>Birthday? Only if you like.</h2>
                    <p>This is optional. You can skip it and start practising.</p>
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        const f = new FormData(e.currentTarget);
                        save((p) => ({ ...p, preferences: { dob: String(f.get("dob")) } }));
                        go("checkout");
                      }}
                    >
                      <Field
                        label="Date of birth · optional"
                        type="date"
                        name="dob"
                        min="1900-01-01"
                        max={new Date().toISOString().slice(0, 10)}
                        defaultValue={profile.preferences?.dob || ""}
                      />
                      <p className="sp-muted">
                        A separate optional preference. It won't change your test price or
                        eligibility.
                      </p>
                      <Action type="submit">Save and find my test</Action>
                      <button
                        type="button"
                        className="sp-text-button"
                        onClick={() => {
                          save((p) => ({ ...p, preferences: { dob: "" } }));
                          go("checkout");
                        }}
                      >
                        Skip for now
                      </button>
                      <button
                        type="button"
                        className="sp-text-button"
                        onClick={() => showCard("education")}
                      >
                        Back
                      </button>
                    </form>
                  </>
                )}
              </section>
            </div>
          )}
          {view === "checkout" && (
            <>
              <Title eyebrow="JEE MAIN PRACTICE" title="Preview checkout">
                Compare the monthly pass with a coupon for a single mock.
              </Title>
              <div className="sp-checkout-grid">
                <section className="sp-checkout-test">
                  <span className="sp-tiny-pill">JEE MAIN · TIMED PRACTICE</span>
                  <h2>JEE Main practice mock</h2>
                  <p>Physics, Chemistry and Mathematics</p>
                  <div className="sp-checkout-details">
                    <span>
                      <Clock3 />
                      180 minutes
                    </span>
                    <span>
                      <BookOpen />
                      Single-choice practice
                    </span>
                    <span>
                      <FileText />
                      Personal report
                    </span>
                  </div>
                  <h3>Here's what you get</h3>
                  <ul className="sp-check-list">
                    <li>
                      <Check /> Full-length, timed practice in the mock library
                    </li>
                    <li>
                      <Check /> Score and subject insights after submission
                    </li>
                    <li>
                      <Check /> A DekhoExams report to keep
                    </li>
                  </ul>
                  <div className="sp-scoring-note">
                    <strong>Know the scoring</strong>
                    <p>
                      Practice scoring gives +4 for a correct answer, −1 for an incorrect answer and
                      0 for a skipped question.
                    </p>
                  </div>
                  <p className="sp-preview-footnote">
                    Try all six original diagnostic questions here. The 180-minute tests are listed
                    in the mock library.
                  </p>
                </section>
                <section className="sp-order-card">
                  <h2>Choose access</h2>
                  <p>School and welcome coupons can cover one mock.</p>
                  <div className="sp-order-line">
                    <span>
                      {coupon && !offerError ? "One free mock" : "Unlimited mocks · 1 month"}
                    </span>
                    <strong>{money(coupon && !offerError ? 0 : MONTHLY_PRICE_PAISE)}</strong>
                  </div>
                  <button
                    className="sp-coupon-trigger"
                    onClick={() => {
                      openCoupons(true);
                      notify("");
                    }}
                  >
                    <span className="sp-icon sp-orange">
                      <Ticket size={21} />
                    </span>
                    <span>
                      <strong>{coupon || "Have a coupon?"}</strong>
                      <small>
                        {coupon
                          ? "Tap to change your offer"
                          : "School code or a little something from us"}
                      </small>
                    </span>
                    <ChevronRight size={20} />
                  </button>
                  {coupon && !offerError && (
                    <div className="sp-savings">
                      <CheckCircle2 size={18} />
                      <span>One free mock unlocked.</span>
                      <button onClick={() => selectCoupon(null)}>Remove</button>
                    </div>
                  )}
                  {offerError && (
                    <p role="alert" className="sp-error">
                      {offerError}
                    </p>
                  )}
                  <div className="sp-total">
                    <span>Amount due</span>
                    <strong>{money(due)}</strong>
                  </div>
                  <p className="sp-muted">
                    {coupon && !offerError
                      ? "Coupon covers one mock. The monthly pass is a separate purchase."
                      : "₹999 per month · unlimited mocks · no automatic renewal"}
                  </p>
                  <Action onClick={startTest}>
                    {due
                      ? `Preview ${money(due)} payment`
                      : answers
                        ? "Resume sample test"
                        : "Start free sample test"}
                  </Action>
                  <div className="sp-safe">
                    <ShieldCheck size={16} />
                    Sample checkout only
                  </div>
                </section>
              </div>
            </>
          )}
          {view === "test" && answers && (
            <>
              <Title eyebrow="JEE MAIN PRACTICE" title="Six-question diagnostic">
                Untimed sample. You can pause and come back while this page stays open.
              </Title>
              <PreviewDiagnostic
                answers={answers}
                flags={flags}
                index={questionIndex}
                onMove={setQuestionIndex}
                onAnswer={(answer) =>
                  setAnswers(answers.map((value, i) => (i === questionIndex ? answer : value)))
                }
                onFlag={() =>
                  setFlags(
                    previewQuestions.map((_, i) => (i === questionIndex ? !flags[i] : !!flags[i])),
                  )
                }
                onSubmit={finish}
              />
            </>
          )}
          {view === "report" && report && (
            <>
              <Title eyebrow="JEE MAIN PRACTICE" title="Your diagnostic report">
                Use this breakdown to choose your next revision session.
              </Title>
              <section className="sp-report" data-preview-report>
                <div className="sp-report-header">
                  <img
                    src="/logos/dekhoexams-wordmark.png"
                    width="170"
                    height="34"
                    alt="DekhoExams"
                  />
                  <div>
                    <strong>JEE Main diagnostic</strong>
                    <small>Six original sample questions</small>
                  </div>
                </div>
                <div className="sp-four">
                  <Metric
                    label="Practice score"
                    value={`${report.score} / ${report.max}`}
                    detail="+4 correct · −1 incorrect"
                  />
                  <Metric
                    label="Accuracy"
                    value={report.accuracy === null ? "—" : `${report.accuracy}%`}
                    detail={
                      report.attempted
                        ? `${report.hits} correct of ${report.attempted} answered`
                        : "No answers submitted"
                    }
                    tone="green"
                  />
                  <Metric
                    label="Answered"
                    value={`${report.attempted} / ${report.graded}`}
                    detail={`${report.skipped} skipped`}
                    tone="orange"
                  />
                  <Metric
                    label="Marks lost"
                    value={String(report.penalty)}
                    detail={`${report.misses} incorrect`}
                    tone="purple"
                  />
                </div>
                <PreviewBreakdown result={report} />
              </section>
              <div className="sp-report-actions">
                <Action onClick={() => window.print()}>
                  <Download size={17} /> Print / save report PDF
                </Action>
                <Action secondary onClick={openDiagnostic}>
                  Retake diagnostic
                </Action>
                <Action secondary onClick={book}>
                  Preview checkout
                </Action>
              </div>
              <PreviewQuestionReview result={report} />
            </>
          )}
          {view === "admin" && (
            <>
              <div className="sp-section-heading">
                <Title eyebrow="PARTNER DESK · DESIGN PREVIEW" title="School and admin preview">
                  See how school coupons and student progress appear in the partner desk.
                </Title>
                <Action onClick={() => showSchoolForm(true)}>
                  <Plus size={17} /> Add a school coupon
                </Action>
              </div>
              <div className="sp-four">
                <Metric
                  label="Sample schools"
                  value={schoolIssued ? "1" : "0"}
                  detail="Codes you create in this preview"
                />
                <Metric
                  label="Profile records"
                  value={profile.contact ? "1" : "0"}
                  detail="Preview memory only"
                  tone="green"
                />
                <Metric
                  label="Submitted samples"
                  value={submitted ? "1" : "0"}
                  detail="No production student activity"
                  tone="orange"
                />
                <Metric
                  label="Payments collected"
                  value="₹0"
                  detail="Payments are not connected"
                  tone="purple"
                />
              </div>
              <div className="sp-admin-panels">
                <section className="sp-table-card">
                  <div className="sp-section-heading">
                    <h2>School access</h2>
                    <Ticket size={20} />
                  </div>
                  {schoolIssued ? (
                    <div className="sp-school-row">
                      <span className="sp-icon sp-blue">
                        <GraduationCap />
                      </span>
                      <div>
                        <h3>{schoolName}</h3>
                        <p>SCHOOL-DEMO · JEE Main</p>
                        <small>Sample limit: 100 students · one attempt each</small>
                      </div>
                      <span className="sp-tiny-pill sp-green">Preview active</span>
                    </div>
                  ) : (
                    <div className="sp-empty">
                      <GraduationCap size={30} />
                      <h3>Start with one school.</h3>
                      <p>
                        Create its code, set a redemption limit and give students a free starting
                        point.
                      </p>
                      <Action secondary onClick={() => showSchoolForm(true)}>
                        Create sample coupon
                      </Action>
                    </div>
                  )}
                  <p className="sp-muted">
                    Live codes will have a scope, expiry, usage limits and an audit trail. School
                    staff receive aggregates unless individual sharing is authorized.
                  </p>
                </section>
                <section className="sp-table-card">
                  <div className="sp-section-heading">
                    <h2>Student journey</h2>
                    <Users size={20} />
                  </div>
                  <div className="sp-progress-row">
                    <span>Contact saved</span>
                    <strong>{profile.contact ? "1" : "0"}</strong>
                  </div>
                  <div className="sp-progress-row">
                    <span>Education saved</span>
                    <strong>{profile.education ? "1" : "0"}</strong>
                  </div>
                  <div className="sp-progress-row">
                    <span>Birthday saved or skipped</span>
                    <strong>{profile.preferences ? "1" : "0"}</strong>
                  </div>
                  <div className="sp-progress-row">
                    <span>Mock submitted</span>
                    <strong>{submitted ? "1" : "0"}</strong>
                  </div>
                  <button className="sp-text-button" onClick={() => showStudent(!studentDetail)}>
                    {studentDetail ? "Hide" : "Inspect"} sample profile
                  </button>
                  {studentDetail && (
                    <div className="sp-profile-summary">
                      <p>
                        <strong>{profile.contact?.name || "No contact saved yet"}</strong>
                      </p>
                      <p>
                        {profile.contact
                          ? "Email and phone are hidden in this admin summary."
                          : "Try the student join flow first."}
                      </p>
                      <p>
                        {profile.education
                          ? `${profile.education.level} · ${profile.education.city}, ${profile.education.state}`
                          : "Education not saved yet"}
                      </p>
                      <p>
                        DOB:{" "}
                        {profile.preferences?.dob
                          ? "Provided · private"
                          : profile.preferences
                            ? "Skipped"
                            : "Not asked yet"}
                      </p>
                    </div>
                  )}
                </section>
              </div>
              <div className="sp-partner-links">
                <a className="sp-button sp-secondary" href="/platform-school">
                  <GraduationCap size={19} /> Open school panel
                </a>
                <a className="sp-button sp-secondary" href="/platform-admin">
                  <LockKeyhole size={18} /> Open owner settings
                </a>
              </div>
              <div className="sp-bottom-note">
                <LockKeyhole size={19} />
                <p>The school panel and owner settings require separate authorized sessions.</p>
              </div>
            </>
          )}
          <footer className="sp-footnote">
            DekhoExams · Built for steady progress.
            <span>Design preview · Website, iOS & Android direction</span>
          </footer>
        </main>
      </div>
      <PreviewDialog open={couponsOpen} onOpenChange={openCoupons} title="Apply a coupon">
        <div className="sp-section-heading">
          <div>
            <span className="sp-eyebrow">A LITTLE SOMETHING FOR YOU</span>
            <h2>Good practice. Better price.</h2>
          </div>
          <button
            autoFocus
            aria-label="Close coupons"
            className="sp-close"
            onClick={() => openCoupons(false)}
          >
            <X />
          </button>
        </div>
        <form
          className="sp-coupon-input"
          onSubmit={(e) => {
            e.preventDefault();
            apply(couponInput);
          }}
        >
          <label className="sr-only" htmlFor="school-code">
            Coupon code
          </label>
          <input
            id="school-code"
            placeholder="Enter a school or offer code"
            value={couponInput}
            onChange={(e) => enterCoupon(e.target.value)}
            maxLength={64}
            autoComplete="off"
          />
          <button type="submit">Apply</button>
        </form>
        <p className="sp-muted">Try SCHOOL-DEMO to preview a school's free access.</p>
        {notice && <p role="status">{notice}</p>}
        <h3>From us, for you</h3>
        {STUDENT_OFFERS.map((o) => {
          const unavailable =
            o.kind === "welcome" ? submitted || welcomeUsed : !submitted || comebackUsed;
          return (
            <article className="sp-offer" key={o.code}>
              <div className="sp-offer-stripe">FREE MOCK</div>
              <div>
                <span className="sp-offer-code">
                  <Ticket size={16} />
                  {o.code}
                </span>
                <h3>{o.title}</h3>
                <p>{o.detail}</p>
                <small>
                  {(o.kind === "welcome" && welcomeUsed) || (o.kind === "comeback" && comebackUsed)
                    ? "Already used"
                    : unavailable
                      ? "Unlocks after your first submission"
                      : "One use per student · one free mock"}
                </small>
              </div>
              <button disabled={unavailable} onClick={() => apply(o.code)}>
                {unavailable ? <LockKeyhole size={16} /> : "Apply"}
              </button>
            </article>
          );
        })}
        <div className="sp-safe">
          <ShieldCheck size={16} />
          The server checks every offer before booking.
        </div>
      </PreviewDialog>
      <PreviewDialog open={schoolForm} onOpenChange={showSchoolForm} title="Create school coupon">
        <div className="sp-section-heading">
          <h2>A free start for your school.</h2>
          <button
            autoFocus
            className="sp-close"
            aria-label="Close school form"
            onClick={() => showSchoolForm(false)}
          >
            <X />
          </button>
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            issueSchool(true);
            showSchoolForm(false);
            notify(
              "Sample coupon SCHOOL-DEMO created in preview memory. Nothing has been issued to a real school.",
            );
          }}
        >
          <Field
            label="School name"
            name="school"
            required
            maxLength={180}
            value={schoolName}
            onChange={(e) => nameSchool(e.target.value)}
          />
          <div className="sp-form-pair">
            <Field
              label="Student limit"
              type="number"
              name="limit"
              defaultValue="100"
              min={1}
              max={10000}
              readOnly
            />
            <Field label="Valid for" name="scope" value="JEE Main" readOnly />
          </div>
          <p className="sp-muted">
            One free attempt per student. This design example uses a fixed code and limit; live
            codes will be generated privately by the server.
          </p>
          <Action type="submit">Create sample coupon</Action>
        </form>
      </PreviewDialog>
    </div>
  );
}

function Field({
  label,
  ...props
}: { label: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="sp-field">
      {label}
      <input {...props} />
    </label>
  );
}

function PreviewDialog({
  open,
  onOpenChange,
  title,
  children,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  title: string;
  children: ReactNode;
}) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="sp-dialog-overlay" />
        <Dialog.Content
          className="student-preview sp-coupon-sheet sp-dialog-position"
          aria-describedby={undefined}
        >
          <Dialog.Title className="sr-only">{title}</Dialog.Title>
          {children}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
