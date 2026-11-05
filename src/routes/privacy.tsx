import { createFileRoute } from "@tanstack/react-router";
import { seoHead } from "@/lib/seo";

export const Route = createFileRoute("/privacy")({
  head: () => seoHead({
    title: "Privacy at Dekhoexams",
    description: "How the Dekhoexams preview uses browser storage and optional external media.",
    path: "privacy",
  }),
  component: PrivacyPage,
});

function PrivacyPage() {
  return (
    <div className="study-home study-lesson">
      <h1>Privacy at Dekhoexams</h1>
      <p className="study-intro">This page describes the current Dekhoexams preview. It should be reviewed before public launch.</p>
      <section>
        <h2>Browser storage</h2>
        <p>The preview uses your browser to remember theme and privacy choices. Existing library features may also save bookmarks, learning progress and drafts in this browser. You can clear saved learning data using the control at the bottom of the site or through your browser settings.</p>
      </section>
      <section>
        <h2>Optional external media</h2>
        <p>External video players stay paused until you allow them in Privacy preferences. Enabling one can share your IP address and browser information with the video provider.</p>
      </section>
      <section>
        <h2>Practice answers</h2>
        <p>Class 1–12 self-check answers, saved lesson IDs and recently opened lessons are stored in this browser. Mistake review uses those saved answers. This preview does not create a school account, sync between devices or submit those answers to a server. Clear saved learning data removes these records.</p>
      </section>
    </div>
  );
}
