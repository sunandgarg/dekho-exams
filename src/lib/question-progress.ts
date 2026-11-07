import { useSyncExternalStore } from "react";
import { questionById } from "./question-bank";

const KEY = "pencil2pen-qbank-v1";
const EVT = "pencil2pen-qbank";
type SavedPyq = { href:string; title:string };
const pyqPath=/^\/past-years\/(?:jee\/question\/[a-z0-9-]+(?:\.htm)?|year-wise\/jee\/jee-main\/[a-z0-9-]+\/[A-Za-z0-9-]+)$/;
type State = { version: 1; pyqs:SavedPyq[]; bookmarks: string[]; attempts: Record<string, { r: number; ok: boolean }> };
const empty = (): State => ({ version: 1, pyqs:[], bookmarks: [], attempts: {} });

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
    const pyqs:SavedPyq[]=Array.isArray(v.pyqs)?v.pyqs.filter((x:SavedPyq)=>x && typeof x.href==="string" && x.href.length<=320 && pyqPath.test(x.href) && typeof x.title==="string" && x.title.length<=260).slice(0,500):[];
    return { version: 1, pyqs, bookmarks, attempts };
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
    togglePyq(item:SavedPyq) {
      const s=parseQState(read());
      s.pyqs=s.pyqs.some(v=>v.href===item.href)?s.pyqs.filter(v=>v.href!==item.href):[item,...s.pyqs].slice(0,500);
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
