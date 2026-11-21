// Split `text` into parts so that words from the question can be highlighted.
// Odd-numbered parts are matches. Safe: returns plain strings, never HTML.
const STOP = new Set([
  "the", "and", "for", "are", "was", "were", "what", "which", "who", "how", "does", "did",
  "this", "that", "with", "from", "can", "you", "your", "about", "have", "has", "give", "say",
]);

export function highlightParts(text, question) {
  const words = [
    ...new Set(
      (question.toLowerCase().match(/[a-z0-9]+/g) || []).filter((w) => w.length > 2 && !STOP.has(w))
    ),
  ];
  if (words.length === 0) return [text];
  const escaped = words.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  return text.split(new RegExp(`\\b(${escaped.join("|")})\\b`, "gi"));
}