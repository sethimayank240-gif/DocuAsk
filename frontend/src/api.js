// Thin wrapper around the Flask REST API. Every call throws Error(message) on failure.
async function request(path, options) {
  let res;
  try {
    res = await fetch(`/api${path}`, options);
  } catch {
    throw new Error("Cannot reach the server. Is the backend running on port 8000?");
  }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

export const getHealth = () => request("/health");
export const listDocuments = () => request("/documents");
export const deleteDocument = (id) => request(`/documents/${id}`, { method: "DELETE" });
export const getHistory = () => request("/history");
export const clearHistory = () => request("/history", { method: "DELETE" });
export const getSuggestions = () => request("/suggestions");
export const askQuestion = (question) =>
  request("/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

export function uploadDocument(file) {
  const form = new FormData();
  form.append("file", file);
  return request("/documents", { method: "POST", body: form });
}