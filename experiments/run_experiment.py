"""
Chunking x Retrieval experiment for a RAG document Q&A system.

Inputs
  docs/       your own .pdf / .txt files (the document collection)
  questions.csv  columns: question,answer_text
                 answer_text = a short exact phrase that appears in the document
                 and answers the question (used to check if a retrieved chunk is correct)

Outputs: results.csv  (chunk_size, overlap, method, Recall@1, Recall@3, Recall@5, MRR)

Usage: python run_experiment.py
Install: pip install scikit-learn pypdf rank_bm25 sentence-transformers numpy
(rank_bm25 and sentence-transformers are optional; methods that are missing are skipped.)
"""
import csv, glob, os, re
import numpy as np
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

CHUNK_SIZES = [128, 256, 512, 1024]   # in words
OVERLAP_RATIO = 0.2
TOP_K = 5

def load_text(path):
    if path.lower().endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
    return open(path, encoding="utf-8", errors="ignore").read()

def norm(s):
    return re.sub(r"\s+", " ", s.lower()).strip()

def tokens(s):
    """Same tokenizer + stop-word list for BM25 as TF-IDF uses, so only the ranking function differs."""
    return [t for t in re.findall(r"[a-z0-9]+", s.lower()) if t not in ENGLISH_STOP_WORDS]

def chunk(text, size, overlap):
    words = norm(text).split()
    step = max(1, size - overlap)
    return [" ".join(words[i:i + size]) for i in range(0, max(1, len(words) - overlap), step)]

def build_retrievers(chunks):
    r = {}
    tf = TfidfVectorizer(stop_words="english"); M = tf.fit_transform(chunks)
    r["TF-IDF"] = lambda q: cosine_similarity(tf.transform([q]), M)[0]
    try:
        from rank_bm25 import BM25Okapi
        bm = BM25Okapi([tokens(c) for c in chunks])
        r["BM25"] = lambda q: np.array(bm.get_scores(tokens(q)))
    except ImportError:
        print("rank_bm25 not installed - skipping BM25")
    try:
        from sentence_transformers import SentenceTransformer
        global _model
        if "_model" not in globals():
            _model = SentenceTransformer("all-MiniLM-L6-v2")
        E = _model.encode(chunks, normalize_embeddings=True, show_progress_bar=False)
        r["Dense (MiniLM)"] = lambda q: E @ _model.encode([q], normalize_embeddings=True)[0]
    except Exception as e:
        print("sentence-transformers unavailable - skipping dense:", type(e).__name__)
    return r

def main():
    text = "\n".join(load_text(p) for p in sorted(glob.glob("docs/*")) if p.lower().endswith((".pdf", ".txt")))
    assert text.strip(), "Put your .pdf/.txt files in docs/"
    qs = list(csv.DictReader(open("questions.csv", encoding="utf-8")))
    assert len(qs) >= 20, "Use at least 20-30 questions for meaningful results"
    rows = []
    for size in CHUNK_SIZES:
        chunks = chunk(text, size, int(size * OVERLAP_RATIO))
        for name, score in build_retrievers(chunks).items():
            hits, rr = {1: 0, 3: 0, 5: 0}, []
            for q in qs:
                order = np.argsort(-score(q["question"]))[:TOP_K]
                gold = norm(q["answer_text"])
                rank = next((i + 1 for i, c in enumerate(order) if gold in chunks[c]), None)
                for k in hits:
                    hits[k] += rank is not None and rank <= k
                rr.append(1 / rank if rank else 0)
            n = len(qs)
            rows.append(dict(chunk_size=size, overlap=int(size * OVERLAP_RATIO), method=name,
                             num_chunks=len(chunks), **{f"Recall@{k}": round(hits[k] / n, 3) for k in hits},
                             MRR=round(float(np.mean(rr)), 3)))
            print(rows[-1])
    with open("results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    print("Saved results.csv")

if __name__ == "__main__":
    main()