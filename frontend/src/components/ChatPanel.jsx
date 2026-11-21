import { useEffect, useRef, useState } from "react";
import { askQuestion } from "../api.js";
import Message from "./Message.jsx";

export default function ChatPanel({ hasDocuments, history, suggestions, onAsked, onClear }) {
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ behavior: "smooth" });
  }, [history.length]);

  async function ask(q) {
    q = q.trim();
    if (!q || busy) return;
    setError("");
    setBusy(true);
    try {
      onAsked(await askQuestion(q));
      setQuestion("");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function submit(e) {
    e.preventDefault();
    ask(question);
  }

  return (
    <section className="panel chat" aria-labelledby="chat-heading">
      <div className="chat-head">
        <h2 id="chat-heading">Ask a question</h2>
        {history.length > 0 && (
          <button className="link-btn" onClick={onClear}>Clear chat</button>
        )}
      </div>
      <div className="thread" aria-live="polite">
        {history.length === 0 && (
          <p className="muted">
            {hasDocuments ? "Ask something about your documents." : "Upload a document first."}
          </p>
        )}
        {history.map((h) => (
          <Message key={`${h.asked_at}-${h.question}`} item={h} />
        ))}
        <div ref={endRef} />
      </div>
      {error && <p className="error" role="alert">{error}</p>}
      {hasDocuments && suggestions.length > 0 && (
        <div className="chips" aria-label="Suggested questions">
          {suggestions.map((s) => (
            <button key={s} className="chip" onClick={() => ask(s)} disabled={busy}>{s}</button>
          ))}
        </div>
      )}
      <form onSubmit={submit} className="ask-form">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. What are the main objectives of the project?"
          maxLength={1000}
          aria-label="Your question"
          disabled={!hasDocuments || busy}
        />
        <button type="submit" disabled={!hasDocuments || busy || !question.trim()}>
          {busy ? "Thinking..." : "Ask"}
        </button>
      </form>
    </section>
  );
}