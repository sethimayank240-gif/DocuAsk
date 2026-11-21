import pytest

from app.chunking import chunk_text
from app.retrieval import Retriever

TEXTS = [
    "The internship lasted six weeks and covered backend and frontend development.",
    "Gradient descent updates model weights using the loss gradient.",
    "The cafeteria opens at nine and serves tea and sandwiches.",
]


def test_chunk_overlap_and_coverage():
    text = " ".join(f"w{i}" for i in range(100))
    chunks = chunk_text(text, size=30, overlap=10)
    assert all(len(c.split()) <= 30 for c in chunks)
    assert chunks[0].split()[-10:] == chunks[1].split()[:10]
    assert set(" ".join(chunks).split()) == set(text.split())  # nothing lost


def test_chunk_validation_and_empty():
    assert chunk_text("   ") == []
    with pytest.raises(ValueError):
        chunk_text("a b c", size=5, overlap=5)


@pytest.mark.parametrize("method", ["tfidf", "bm25"])
def test_retrieval_finds_right_chunk(method):
    r = Retriever(method)
    r.build(TEXTS)
    top = r.search("How long was the internship?", k=2)
    assert top and top[0][0] == 0


@pytest.mark.parametrize("method", ["tfidf", "bm25"])
def test_no_match_returns_empty(method):
    r = Retriever(method)
    r.build(TEXTS)
    assert r.search("zzzz qqqq", k=3) == []
