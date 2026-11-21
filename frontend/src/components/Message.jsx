import { useState } from "react";
import { highlightParts } from "../highlight.js";

function Highlighted({ text, question }) {
  return highlightParts(text, question).map((part, i) =>
    i % 2 === 1 ? <mark key={i}>{part}</mark> : part
  );
}

export default function Message({ item }) {
  const [open, setOpen] = useState(false);
  return (
    <article className="turn">
      <p className="bubble user">{item.question}</p>
      <div className="bubble bot">
        <p className="answer">{item.answer}</p>
        {item.sources.length > 0 && (
          <>
            <button className="link-btn" onClick={() => setOpen(!open)} aria-expanded={open}>
              {open ? "Hide" : "Show"} {item.sources.length} source{item.sources.length === 1 ? "" : "s"}
            </button>
            {open && (
              <ol className="sources">
                {item.sources.map((s, i) => (
                  <li key={i}>
                    <div className="src-head">
                      [{i + 1}] {s.doc_name}, page {s.page}
                      <span className="muted"> · score {s.score}</span>
                    </div>
                    <blockquote>
                      <Highlighted text={s.text} question={item.question} />
                    </blockquote>
                  </li>
                ))}
              </ol>
            )}
          </>
        )}
        <p className="meta muted">{item.latency_ms} ms · {item.mode}</p>
      </div>
    </article>
  );
}