import { useId, useState } from "react";
import { Button } from "@/components/ui/button";

const instructions = [
  "savedNext = cursor.next;",
  "cursor.next = reversedHead;",
  "reversedHead = cursor;",
  "cursor = savedNext;",
];
const explanations = [
  "Keep the unprocessed chain reachable before changing any link.",
  "Point this node toward the reversed chain. Its old next link is replaced.",
  "Move the reversed head onto this node. No node is allocated or copied.",
  "Continue from the saved reference. The next iteration handles that node.",
];

export function LinkedListReversal() {
  const markerId = useId().replace(/:/g, "");
  const [count, setCount] = useState(4);
  const [step, setStep] = useState(0);
  const [answer, setAnswer] = useState<number | null>(null);
  const total = count * 4;
  const complete = step === total;
  const processed = Math.floor(step / 4);
  const phase = step % 4;
  const changed = Math.min(count, processed + (phase >= 2 ? 1 : 0));
  const previous = processed + (phase >= 3 ? 1 : 0) - 1;
  const saved = phase >= 1 ? processed + 1 : processed;
  const values = Array.from({ length: count }, (_, index) => (index + 1) * 32);
  const nodeName = (index: number) =>
    index < 0 || index >= count ? "null" : String(values[index]);
  const reversed = values.slice(0, changed).reverse();
  const pending = values.slice(changed);
  const message =
    count === 0
      ? "The head is null. The loop never runs; the result is null."
      : complete
        ? `Finished: ${values.at(-1)} is the new head. Every link has been reversed.`
        : step === 0
          ? "Start with an empty reversed chain. Cursor points to the original head."
          : explanations[(step - 1) % 4]!;
  function restart(size = count) {
    setCount(size);
    setStep(0);
  }
  return (
    <section className="reversal-lab my-7 rounded-lg border" aria-labelledby="linked-list-reversal">
      <div className="p-4 sm:p-5">
        <p className="visual-eyebrow">02 / Follow the algorithm</p>
        <h2 id="linked-list-reversal" className="font-display text-xl font-bold">
          Reverse one link at a time
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          A custom singly linked list, drawn from scratch. This pointer simulation does not execute
          Java or expose the private nodes of java.util.LinkedList, which is doubly linked.
        </p>
        <div className="visual-key mt-4" aria-label="Choose a list size">
          {[4, 1, 0].map((size) => (
            <button
              key={size}
              type="button"
              aria-pressed={count === size}
              onClick={() => restart(size)}
            >
              {size === 4 ? "Four nodes" : size === 1 ? "One node" : "Empty list"}
            </button>
          ))}
        </div>
        <figure className="reversal-figure mt-4">
          <svg
            viewBox="0 0 480 218"
            role="img"
            aria-label={`Reversed chain: ${reversed.join(" to ") || "empty"}. Unprocessed chain: ${pending.join(" to ") || "empty"}.`}
          >
            <defs>
              <marker
                id={markerId}
                viewBox="0 0 10 10"
                refX="9"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke" />
              </marker>
            </defs>
            {[reversed, pending].map((chain, row) => (
              <g key={row} className={row === 0 ? "reversed-chain" : "pending-chain"}>
                <text x="18" y={row * 105 + 23} className="chain-caption">
                  {row === 0 ? "REVERSED LINKS" : "UNPROCESSED LINKS"}
                </text>
                {!chain.length && (
                  <text x="18" y={row * 105 + 65} className="chain-null">
                    null
                  </text>
                )}
                {chain.map((value, index) => (
                  <g key={value}>
                    <rect x={index * 100 + 18} y={row * 105 + 37} width="70" height="50" rx="6" />
                    <text
                      x={index * 100 + 53}
                      y={row * 105 + 69}
                      textAnchor="middle"
                      className="chain-value"
                    >
                      {value}
                    </text>
                    <line
                      x1={index * 100 + 91}
                      y1={row * 105 + 62}
                      x2={index * 100 + 111}
                      y2={row * 105 + 62}
                      markerEnd={`url(#${markerId})`}
                    />
                  </g>
                ))}
                {!!chain.length && (
                  <text x={chain.length * 100 + 18} y={row * 105 + 68} className="chain-null">
                    null
                  </text>
                )}
              </g>
            ))}
          </svg>
          <figcaption className="px-4 pb-4 text-sm">
            Values stay in their nodes. Only next references change. The two rows show separate
            chains, not new copies of the list.
          </figcaption>
        </figure>
        <dl className="pointer-registers mt-4">
          <div className="visual-mint">
            <dt>reversedHead</dt>
            <dd>{nodeName(previous)}</dd>
          </div>
          <div className="visual-blue">
            <dt>cursor</dt>
            <dd>{nodeName(processed)}</dd>
          </div>
          <div className="visual-peach">
            <dt>savedNext</dt>
            <dd>{step === 0 ? "not assigned" : nodeName(saved)}</dd>
          </div>
        </dl>
        <div className="reversal-instructions mt-4" aria-label="Pointer assignments">
          <pre>
            <code className="language-java">
              {instructions.map((line, index) => (
                <span
                  key={line}
                  className={
                    step > 0 && !complete && index === (step - 1) % 4 ? "active-instruction" : ""
                  }
                >
                  {line}
                  {"\n"}
                </span>
              ))}
            </code>
          </pre>
          <p className="p-3 text-sm" role="status" aria-live="polite">
            {message}
          </p>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <Button variant="outline" disabled={step === 0} onClick={() => setStep(step - 1)}>
            Previous step
          </Button>
          <Button disabled={complete} onClick={() => setStep(step + 1)}>
            Next step
          </Button>
          <Button variant="ghost" onClick={() => restart()}>
            Restart reversal
          </Button>
          <span className="text-xs font-semibold">
            {step} / {total} assignments
          </span>
        </div>
        <p className="mt-3 text-sm text-muted-foreground">
          Time: O(n). Extra space: O(1). This model assumes an acyclic list.
        </p>
      </div>
      <fieldset className="prediction-check border-t p-4 sm:p-5">
        <legend className="float-left mb-3 w-full font-bold">Predict before you continue</legend>
        <p className="clear-both text-sm">Why save cursor.next before replacing it?</p>
        <div className="mt-3 flex flex-col gap-2">
          {[
            "To keep the rest of the list reachable",
            "To allocate a copy of the next node",
            "To sort the node values",
          ].map((choice, index) => (
            <button
              type="button"
              key={choice}
              aria-pressed={answer === index}
              onClick={() => setAnswer(index)}
            >
              {choice}
            </button>
          ))}
        </div>
        {answer !== null && (
          <p role="status" className="mt-3 text-sm">
            <strong>{answer === 0 ? "Correct." : "Try again."}</strong> Replacing the next reference
            can disconnect the remaining chain. Saving a reference keeps it reachable; it does not
            copy a node.
          </p>
        )}
      </fieldset>
    </section>
  );
}
