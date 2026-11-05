import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";

const key = "penpencil-consent-v1";
const changed = "penpencil-consent-change";
type Choice = { externalMedia: boolean; version: 1 };
function readChoice(): Choice | null {
  try {
    const value = JSON.parse(localStorage.getItem(key) ?? "null");
    return value?.version === 1 && typeof value.externalMedia === "boolean" ? value : null;
  } catch {
    return null;
  }
}
function useChoice() {
  const [choice, setChoice] = useState<Choice | null>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const refresh = () => setChoice(readChoice());
    refresh();
    setReady(true);
    window.addEventListener(changed, refresh);
    window.addEventListener("storage", refresh);
    return () => {
      window.removeEventListener(changed, refresh);
      window.removeEventListener("storage", refresh);
    };
  }, []);
  return { choice, ready };
}
export function PrivacyControls() {
  const { choice, ready } = useChoice();
  const [open, setOpen] = useState(false);
  const [media, setMedia] = useState(false);
  const [notice, setNotice] = useState("");
  function save(externalMedia: boolean) {
    try {
      localStorage.setItem(key, JSON.stringify({ externalMedia, version: 1 }));
    } catch {
      setNotice("Preferences could not be saved. External media remains blocked.");
      return;
    }
    window.dispatchEvent(new Event(changed));
    setOpen(false);
  }
  return (
    <section aria-label="Privacy controls" className="border-t bg-background px-5 py-5">
      <div className="mx-auto max-w-[1320px]">
        <div className="flex flex-wrap items-center gap-4 text-sm">
          <button
            className="underline underline-offset-4"
            onClick={() => {
              setMedia(choice?.externalMedia ?? false);
              setOpen(!open);
            }}
          >
            Privacy preferences
          </button>
          <button
            className="underline underline-offset-4"
            onClick={() => {
              if (
                !window.confirm(
                  "Delete saved bookmarks, progress, quiz results, display name and drafts from this browser?",
                )
              )
                return;
              localStorage.removeItem("aitrove-ozi-preview-v1");
              localStorage.removeItem("penpencil-learning-v1");
              window.dispatchEvent(new Event("penpencil-progress"));
              window.dispatchEvent(new Event("aitrove-ozi-preview-change"));
              setNotice("Saved learning data cleared from this browser.");
            }}
          >
            Clear saved learning data
          </button>
          <a href="/privacy" className="underline underline-offset-4">
            Storage details
          </a>
        </div>
        {ready && (!choice || open) && (
          <div className="mt-4 max-w-3xl border p-5" aria-labelledby="privacy-heading">
            <h2 id="privacy-heading" className="text-lg font-bold">
              Your privacy choices
            </h2>
            <p className="my-3 text-sm">
              This site uses browser storage for your theme, privacy choices and learning actions
              you choose to save. No analytics or advertising trackers are installed. External
              videos stay blocked unless you allow them.
            </p>
            {open && (
              <label className="mb-4 flex items-center gap-3 text-sm">
                <input
                  type="checkbox"
                  checked={media}
                  onChange={(e) => setMedia(e.target.checked)}
                />
                Allow external video providers to load
              </label>
            )}
            <div className="flex flex-wrap gap-3">
              <Button variant="outline" onClick={() => save(false)}>
                Reject optional media
              </Button>
              <Button variant="outline" onClick={() => save(true)}>
                Allow external media
              </Button>
              {open ? (
                <Button onClick={() => save(media)}>Save preferences</Button>
              ) : (
                <Button variant="outline" onClick={() => setOpen(true)}>
                  Customize
                </Button>
              )}
            </div>
            <p className="mt-3 text-xs">
              You can change this choice here at any time.{" "}
              <a href="/privacy" className="underline">
                Privacy policy
              </a>
            </p>
          </div>
        )}
        {notice && (
          <p className="mt-3 text-sm" role="status">
            {notice}
          </p>
        )}
      </div>
    </section>
  );
}
export function FormPrivacyNotice() {
  return (
    <div className="grid gap-3 text-sm">
      <p>This preview does not send or store these form fields. Contact forms are not active yet.</p>
      <label className="flex items-start gap-3">
        <input type="checkbox" required className="mt-1" />{" "}
        <span>
          I have read the{" "}
          <a className="underline" href="/privacy">
            privacy notice
          </a>{" "}
          and understand how this preview handles my information.
        </span>
      </label>
    </div>
  );
}
export function SafeMedia({ url, title }: { url: string; title: string }) {
  const { choice, ready } = useChoice();
  if (!ready)
    return (
      <div className="aspect-video p-6 text-white" role="status">
        Preparing video controls…
      </div>
    );
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return <p className="p-6 text-white">A valid video URL has not been published.</p>;
  }
  const host = parsed.hostname;
  const own = typeof window !== "undefined" && parsed.origin === window.location.origin;
  const file = /\.(mp4|webm)$/i.test(parsed.pathname);
  const trusted = [
    "www.youtube-nocookie.com",
    "www.youtube.com",
    "youtube.com",
    "player.vimeo.com",
  ].includes(host);
  if (parsed.protocol !== "https:" || (!trusted && !(own && file)))
    return (
      <p className="p-6 text-white">
        This media source is not supported. Please ask the editor to use a supported provider.
      </p>
    );
  if (own && file)
    return (
      <video src={url} controls preload="none" aria-label={title} className="aspect-video w-full" />
    );
  if (!choice?.externalMedia)
    return (
      <div className="grid aspect-video place-items-center p-6 text-center text-white">
        <div>
          <h2 className="font-bold">External video is paused</h2>
          <p className="mt-2 text-sm">
            Loading this video shares your IP address and browser information with {host}.
          </p>
          <p className="mt-2 text-sm">Use Privacy preferences below to allow external media.</p>
          <a className="mt-3 inline-block underline" href="/privacy">
            Read about external media
          </a>
        </div>
      </div>
    );
  if (host.includes("youtube")) parsed.hostname = "www.youtube-nocookie.com";
  return (
    <iframe
      src={parsed.toString()}
      title={title}
      className="aspect-video w-full"
      sandbox="allow-scripts allow-same-origin allow-presentation"
      referrerPolicy="no-referrer"
      allow="encrypted-media; picture-in-picture; fullscreen"
      loading="lazy"
    />
  );
}
