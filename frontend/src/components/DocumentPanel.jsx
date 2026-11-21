import { useRef, useState } from "react";
import { uploadDocument, deleteDocument } from "../api.js";

export default function DocumentPanel({ documents, onChanged }) {
  const inputRef = useRef(null);
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");

  async function handleFiles(files) {
    if (files.length === 0) return;
    setError("");
    setBusy(true);
    const failures = [];
    for (const file of files) {
      try {
        await uploadDocument(file);
      } catch (e) {
        failures.push(`${file.name}: ${e.message}`);
      }
    }
    if (failures.length) setError(failures.join(" | "));
    onChanged();
    setBusy(false);
    if (inputRef.current) inputRef.current.value = "";
  }

  async function remove(id) {
    setError("");
    try {
      await deleteDocument(id);
      onChanged();
    } catch (e) {
      setError(e.message);
    }
  }

  function onDrop(e) {
    e.preventDefault();
    setDragging(false);
    if (!busy) handleFiles([...e.dataTransfer.files]);
  }

  return (
    <section className="panel" aria-labelledby="docs-heading">
      <h2 id="docs-heading">Documents</h2>
      <label
        className={`dropzone${dragging ? " dragging" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.txt"
          multiple
          disabled={busy}
          onChange={(e) => handleFiles([...e.target.files])}
        />
        <span>{busy ? "Processing..." : dragging ? "Drop to upload" : "Drag files here or click to choose (PDF, TXT)"}</span>
      </label>
      {error && <p className="error" role="alert">{error}</p>}
      {documents.length === 0 ? (
        <p className="muted">No documents yet. Upload one to start asking questions.</p>
      ) : (
        <ul className="doc-list">
          {documents.map((d) => (
            <li key={d.id}>
              <div>
                <strong>{d.name}</strong>
                <span className="muted"> {d.pages} page{d.pages === 1 ? "" : "s"} · {d.chunks} chunks</span>
              </div>
              <button className="link-btn" onClick={() => remove(d.id)} aria-label={`Delete ${d.name}`}>
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}