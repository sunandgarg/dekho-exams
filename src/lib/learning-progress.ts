import { useSyncExternalStore } from "react";
import { RESOURCES, resourceById } from "./education-catalog";

export const LEARNING_STORAGE_KEY = "penpencil-learning-v1";
type Progress = {
  version: 1;
  saved: string[];
  recent: string[];
  answers: Record<string, Record<number, number>>;
};
const empty = (): Progress => ({ version: 1, saved: [], recent: [], answers: {} });
export function parseProgress(raw: string | null): Progress {
  try {
    const value = JSON.parse(raw ?? "null");
    if (!value || value.version !== 1) return empty();
    const ids = (list: unknown) =>
      Array.isArray(list)
        ? [
            ...new Set(
              list.filter((id): id is string => typeof id === "string" && !!resourceById(id)),
            ),
          ].slice(0, 100)
        : [];
    const answers: Progress["answers"] = {};
    for (const r of RESOURCES) {
      const key = `${r.id}@${r.version}`;
      const record = value.answers?.[key];
      if (!record || typeof record !== "object") continue;
      answers[key] = {};
      r.lesson.questions.forEach((q, index) => {
        if (
          Number.isInteger(record[index]) &&
          record[index] >= 0 &&
          record[index] < q.choices.length
        )
          answers[key]![index] = record[index];
      });
    }
    return { version: 1, saved: ids(value.saved), recent: ids(value.recent), answers };
  } catch {
    return empty();
  }
}
function snapshot() {
  try {
    return localStorage.getItem(LEARNING_STORAGE_KEY);
  } catch {
    return null;
  }
}
function subscribe(callback: () => void) {
  window.addEventListener("storage", callback);
  window.addEventListener("penpencil-progress", callback);
  return () => {
    window.removeEventListener("storage", callback);
    window.removeEventListener("penpencil-progress", callback);
  };
}
export function useLearningProgress() {
  const raw = useSyncExternalStore(subscribe, snapshot, () => null);
  return parseProgress(raw);
}
export function updateProgress(update: (current: Progress) => Progress): boolean {
  try {
    localStorage.setItem(LEARNING_STORAGE_KEY, JSON.stringify(update(parseProgress(snapshot()))));
    window.dispatchEvent(new Event("penpencil-progress"));
    return true;
  } catch {
    return false;
  }
}
