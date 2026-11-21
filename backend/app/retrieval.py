"""Rank chunks against a question. Methods: tfidf, bm25, dense (optional)."""
import math
import re
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = {"the", "a", "an", "is", "are", "of", "to", "in", "and", "or", "for", "on",
         "what", "which", "who", "how", "does", "do", "did", "was", "were", "it",
         "this", "that", "with", "as", "by", "at", "from", "be", "can"}


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in _STOP]


class BM25:
    """Okapi BM25 (Robertson & Zaragoza) - small dependency-free implementation."""

    def __init__(self, docs: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = [Counter(d) for d in docs]
        self.len = np.array([len(d) for d in docs], dtype=float)
        self.avg = self.len.mean() if len(docs) else 0.0
        df = Counter(t for d in self.docs for t in d)
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query: list[str]) -> np.ndarray:
        out = np.zeros(len(self.docs))
        for i, d in enumerate(self.docs):
            norm = self.k1 * (1 - self.b + self.b * self.len[i] / (self.avg or 1))
            for t in query:
                if t in d:
                    out[i] += self.idf[t] * d[t] * (self.k1 + 1) / (d[t] + norm)
        return out


class Retriever:
    def __init__(self, method: str = "bm25"):
        if method not in {"tfidf", "bm25", "dense"}:
            raise ValueError("method must be tfidf, bm25 or dense")
        self.method = method
        self.texts: list[str] = []
        self._tfidf = self._matrix = self._bm25 = self._emb = self._model = None

    def build(self, texts: list[str]) -> None:
        self.texts = list(texts)
        if not texts:
            return
        if self.method == "tfidf":
            self._tfidf = TfidfVectorizer(stop_words="english")
            self._matrix = self._tfidf.fit_transform(texts)
        elif self.method == "bm25":
            self._bm25 = BM25([tokenize(t) for t in texts])
        else:
            from sentence_transformers import SentenceTransformer  # optional dependency
            self._model = self._model or SentenceTransformer("all-MiniLM-L6-v2")
            self._emb = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    def search(self, query: str, k: int = 4) -> list[tuple[int, float]]:
        """Return up to k (chunk_index, score) pairs with score > 0, best first."""
        if not self.texts:
            return []
        if self.method == "tfidf":
            scores = cosine_similarity(self._tfidf.transform([query]), self._matrix)[0]
        elif self.method == "bm25":
            scores = self._bm25.scores(tokenize(query))
        else:
            scores = self._emb @ self._model.encode([query], normalize_embeddings=True)[0]
        order = np.argsort(-scores)[:k]
        return [(int(i), float(scores[i])) for i in order if scores[i] > 0]
