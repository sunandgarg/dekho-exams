import { useSyncExternalStore } from "react";
import { questionById } from "./question-bank";

const KEY = "pencil2pen-qbank-v1";
const EVT = "pencil2pen-qbank";
type State = { version: 1; bookmarks: string[]; attempts: Record<string, { r: number; ok: boolean }> };
const empty = (): State => ({ version: 1, bookmarks: [], attempts: {} });

export function parseQState(raw: string | null): State {
  try {
    const v = JSON.parse(raw ?? "null");
    if (!v || v.version !== 1) return empty();
    const bookmarks = Array.isArray(v.bookmarks)
      ? [...new Set(v.bookmarks.filter((id: unknown) => typeof id === "string" && questionById(id)))] as string[]
      : [];
    const attempts: State["attempts"] = {};
    for (const [k, a] of Object.entries(v.attempts ?? {})) {
      const rec = a as { r?: unknown; ok?: unknown };
      if (questionById(k) && typeof rec?.r === "number" && typeof rec?.ok === "boolean") attempts[k] = { r: rec.r, ok: rec.ok };
    }
    return { version: 1, bookmarks, attempts };
  } catch {
    return empty();
  }
}
const read = () => { try { return localStorage.getItem(KEY); } catch { return null; } };
const sub = (cb: () => void) => {
  window.addEventListener("storage", cb);
  window.addEventListener(EVT, cb);
  return () => { window.removeEventListener("storage", cb); window.removeEventListener(EVT, cb); };
};
function write(s: State): boolean {
  try { localStorage.setItem(KEY, JSON.stringify(s)); window.dispatchEvent(new Event(EVT)); return true; }
  catch { return false; }
}
export function useQuestionProgress() {
  const raw = useSyncExternalStore(sub, read, () => null);
  const state = parseQState(raw);
  return {
    state,
    ready: typeof window !== "undefined",
    toggleBookmark(id: string) {
      const s = parseQState(read());
      s.bookmarks = s.bookmarks.includes(id) ? s.bookmarks.filter((b) => b !== id) : [id, ...s.bookmarks];
      return write(s);
    },
    record(id: string, r: number, ok: boolean) {
      const s = parseQState(read());
      s.attempts[id] = { r, ok };
      return write(s);
    },
    reset() { return write(empty()); },
  };
}
