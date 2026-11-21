"""Document store: keeps chunks in memory and persists them to a JSON file."""
import json
import threading
import time
import uuid

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .chunking import chunk_text
from .retrieval import Retriever


class DocumentStore:
    def __init__(self, cfg):
        self.cfg = cfg
        self.path = cfg.DATA_DIR / "store.json"
        self.lock = threading.Lock()
        self.docs: dict[str, dict] = {}
        self.history: list[dict] = []
        self.chunks: list[dict] = []
        self.retriever = Retriever(cfg.RETRIEVER)
        self._load()
        self._rebuild()

    # ---- persistence
    def _load(self):
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                self.docs, self.history = data.get("docs", {}), data.get("history", [])
            except (json.JSONDecodeError, OSError):
                self.docs, self.history = {}, []

    def _save(self):
        self.cfg.DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"docs": self.docs, "history": self.history}), encoding="utf-8")
        tmp.replace(self.path)

    def _rebuild(self):
        self.chunks = [c for d in self.docs.values() for c in d["chunks"]]
        self.retriever.build([c["text"] for c in self.chunks])

    # ---- documents
    def add_document(self, name: str, pages: list[str]) -> dict:
        doc_id = uuid.uuid4().hex[:12]
        chunks = []
        for page_no, text in enumerate(pages, 1):  # chunk within a page so citations have a page
            for piece in chunk_text(text, self.cfg.CHUNK_SIZE, self.cfg.CHUNK_OVERLAP):
                chunks.append({"doc_id": doc_id, "doc_name": name, "page": page_no, "text": piece})
        if not chunks:
            raise ValueError("No readable text found (scanned PDFs need OCR).")
        doc = {"id": doc_id, "name": name, "pages": len(pages), "chunks": chunks,
               "uploaded_at": int(time.time())}
        with self.lock:
            self.docs[doc_id] = doc
            self._rebuild()
            self._save()
        return self.summary(doc)

    def delete_document(self, doc_id: str) -> bool:
        with self.lock:
            if doc_id not in self.docs:
                return False
            del self.docs[doc_id]
            self._rebuild()
            self._save()
            return True

    @staticmethod
    def summary(doc: dict) -> dict:
        return {"id": doc["id"], "name": doc["name"], "pages": doc["pages"],
                "chunks": len(doc["chunks"]), "uploaded_at": doc["uploaded_at"]}

    def list_documents(self) -> list[dict]:
        return sorted((self.summary(d) for d in self.docs.values()),
                      key=lambda d: d["uploaded_at"], reverse=True)

    # ---- query
    def search(self, question: str, k: int) -> list[dict]:
        hits = self.retriever.search(question, k)
        return [{**self.chunks[i], "score": round(s, 4)} for i, s in hits]

    def add_history(self, entry: dict):
        with self.lock:
            self.history = (self.history + [entry])[-50:]
            self._save()

    def clear_history(self):
        with self.lock:
            self.history = []
            self._save()

    def suggestions(self, n: int = 4) -> list[str]:
        """Example questions built from the most distinctive words in the uploaded documents."""
        texts = [c["text"] for c in self.chunks]
        if not texts:
            return []
        vec = TfidfVectorizer(stop_words="english", token_pattern=r"(?u)\b[a-zA-Z]{4,}\b", max_features=500)
        try:
            matrix = vec.fit_transform(texts)
        except ValueError:  # no usable words
            return []
        scores = np.asarray(matrix.sum(axis=0)).ravel()
        terms = vec.get_feature_names_out()
        return [f"What does the document say about {terms[i]}?" for i in np.argsort(-scores)[:n]]