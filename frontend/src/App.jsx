import { useCallback, useEffect, useState } from "react";
import { clearHistory, getHealth, getHistory, getSuggestions, listDocuments } from "./api.js";
import DocumentPanel from "./components/DocumentPanel.jsx";
import ChatPanel from "./components/ChatPanel.jsx";

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [history, setHistory] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [health, setHealth] = useState(null);
  const [error, setError] = useState("");

  const refreshDocuments = useCallback(async () => {
    try {
      setDocuments(await listDocuments());
      setSuggestions(await getSuggestions());
    } catch (e) {
      setError(e.message);
    }
  }, []);

  useEffect(() => {
    refreshDocuments();
    getHealth().then(setHealth).catch((e) => setError(e.message));
    // the server keeps the last 50 questions (newest first); show them oldest first
    getHistory().then((h) => setHistory([...h].reverse())).catch(() => {});
  }, [refreshDocuments]);

  const addTurn = (turn) => setHistory((h) => [...h, turn]);

  async function handleClear() {
    try {
      await clearHistory();
      setHistory([]);
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div className="app">
      <header>
        <h1>DocuAsk</h1>
        <p className="muted">Ask questions about your documents and see exactly where the answer came from.</p>
        {health && (
          <p className="strip muted">
            Retriever: <strong>{health.retriever.toUpperCase()}</strong> · Answers:{" "}
            <strong>{health.llm_configured ? "LLM" : "excerpts only"}</strong>
          </p>
        )}
        {health && !health.llm_configured && (
          <p className="notice">
            No LLM key configured: answers show the best matching excerpt. Add LLM_API_KEY to the backend .env for full answers.
          </p>
        )}
        {error && <p className="error" role="alert">{error}</p>}
      </header>
      <main>
        <DocumentPanel documents={documents} onChanged={refreshDocuments} />
        <ChatPanel
          hasDocuments={documents.length > 0}
          history={history}
          suggestions={suggestions}
          onAsked={addTurn}
          onClear={handleClear}
        />
      </main>
    </div>
  );
}