import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function LinkedListDemo() {
  const [values, setValues] = useState(["Read", "Code", "Review"]);
  const [value, setValue] = useState("Test");
  const [message, setMessage] = useState("Three nodes, linked in both directions.");
  function add(first: boolean) {
    const text = value.trim();
    if (!text || values.length >= 6) return;
    setValues(first ? [text, ...values] : [...values, text]);
    setMessage(
      `${first ? "addFirst" : "addLast"}("${text}"): a new node is linked at the ${first ? "head" : "tail"}.`,
    );
  }
  function poll(first: boolean) {
    const removed = first ? values[0] : values[values.length - 1];
    setValues(first ? values.slice(1) : values.slice(0, -1));
    setMessage(
      `${first ? "pollFirst" : "pollLast"}() returns ${removed ? `"${removed}"` : "null"}.`,
    );
  }
  return (
    <section
      aria-labelledby="linked-list-demo"
      className="linked-list-visual my-7 rounded-lg border p-4 sm:p-5"
    >
      <p className="visual-eyebrow">01 / Node playground</p>
      <h2 id="linked-list-demo" className="font-display text-xl font-bold">
        See the links change
      </h2>
      <p className="mt-2 text-sm text-muted-foreground">
        A visual model of a doubly linked list. This demonstrates endpoint operations; it does not
        execute Java. Up to six nodes fit in this demo.
      </p>
      <div className="visual-key mt-4" aria-label="Diagram key">
        <span className="visual-mint">Head: first node</span>
        <span className="visual-blue">Middle: two neighbours</span>
        <span className="visual-peach">Tail: last node</span>
      </div>
      <div
        className="my-5 overflow-x-auto pb-2"
        role="region"
        aria-label="Doubly linked list nodes"
        tabIndex={0}
      >
        <ol className="flex w-max min-w-full items-center gap-2">
          <li className="text-xs text-muted-foreground">null</li>
          {values.map((text, i) => (
            <li key={i} className="flex items-center gap-2">
              <span aria-hidden="true" className="node-arrow">
                ⇄
              </span>
              <div
                className={`list-node min-w-28 rounded border text-center ${i === 0 ? "visual-mint" : i === values.length - 1 ? "visual-peach" : "visual-blue"}`}
              >
                <div className="node-label border-b px-3 py-1 text-xs font-semibold">
                  {i === 0 ? "head" : i === values.length - 1 ? "tail" : `node ${i + 1}`}
                  {values.length === 1 ? " / tail" : ""}
                </div>
                <div className="px-3 py-3 font-mono text-sm font-bold">{text}</div>
                <div className="node-pointers border-t px-2 py-1 text-[11px]">
                  prev: {i === 0 ? "null" : i} · next: {i === values.length - 1 ? "null" : i + 2}
                </div>
              </div>
            </li>
          ))}
          <li className="text-xs text-muted-foreground">
            {values.length ? "⇄ null" : "Empty list: head = tail = null"}
          </li>
        </ol>
      </div>
      <div className="flex flex-wrap items-end gap-2">
        <label className="w-36 text-xs font-semibold">
          New node value
          <Input
            value={value}
            onChange={(e) => setValue(e.target.value)}
            maxLength={12}
            className="mt-1 bg-card"
          />
        </label>
        <Button
          variant="outline"
          onClick={() => add(true)}
          disabled={!value.trim() || values.length >= 6}
        >
          addFirst
        </Button>
        <Button
          variant="outline"
          onClick={() => add(false)}
          disabled={!value.trim() || values.length >= 6}
        >
          addLast
        </Button>
        <Button variant="outline" onClick={() => poll(true)}>
          pollFirst
        </Button>
        <Button variant="outline" onClick={() => poll(false)}>
          pollLast
        </Button>
        <Button
          variant="ghost"
          onClick={() => {
            setValues(["Read", "Code", "Review"]);
            setMessage("Reset to three nodes.");
          }}
        >
          Reset
        </Button>
      </div>
      <p className="node-operation mt-4 text-sm" role="status">
        {message}
      </p>
      <p className="mt-2 font-mono text-xs">size() = {values.length}</p>
      <p className="mt-3 text-sm text-muted-foreground">
        Try removing every node, then poll once more. An empty list returns null; a one-node list
        shares its head and tail.
      </p>
    </section>
  );
}
