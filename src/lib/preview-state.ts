import { useEffect, useState } from "react";
export type SavedItem = { path: string; title: string; type: string };
export type QuizResult = { answers: number[]; submittedAt: string };
export type PreviewState = {
  bookmarks: SavedItem[];
  completed: string[];
  quizzes: Record<string, QuizResult>;
  settings: { displayName: string; dailyGoal: number };
  drafts: Record<string, string>;
};
const empty = (): PreviewState => ({
  bookmarks: [],
  completed: [],
  quizzes: {},
  settings: { displayName: "Learner", dailyGoal: 20 },
  drafts: {},
});
const key = "aitrove-ozi-preview-v1";
const eventName = "aitrove-ozi-preview-change";
export function readPreview(): PreviewState {
  try {
    const data = JSON.parse(localStorage.getItem(key) ?? "null");
    if (
      !data ||
      !Array.isArray(data.bookmarks) ||
      !Array.isArray(data.completed) ||
      !data.quizzes ||
      !data.settings ||
      !data.drafts
    )
      return empty();
    return data;
  } catch {
    return empty();
  }
}
export function usePreview() {
  const [state, setState] = useState<PreviewState>(empty);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const refresh = () => setState(readPreview());
    refresh();
    setReady(true);
    window.addEventListener(eventName, refresh);
    window.addEventListener("storage", refresh);
    return () => {
      window.removeEventListener(eventName, refresh);
      window.removeEventListener("storage", refresh);
    };
  }, []);
  function update(fn: (previous: PreviewState) => PreviewState) {
    const next = fn(readPreview());
    try {
      localStorage.setItem(key, JSON.stringify(next));
      window.dispatchEvent(new Event(eventName));
    } catch {
      setState(next);
    }
  }
  return { state, update, ready };
}
