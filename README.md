# DocuAsk - RAG Document Question-Answering Assistant

Upload PDF/TXT documents, ask questions in plain English, and get answers with the exact
source passages (document name + page). Built for the AIML summer internship report.

```
rag-doc-qa/
├── backend/                 Flask REST API + retrieval pipeline
│   ├── app/
│   │   ├── __init__.py      app factory, CORS, error handlers
│   │   ├── config.py        settings from environment / .env
│   │   ├── ingestion.py     PDF/TXT text extraction (per page)
│   │   ├── chunking.py      overlapping word-window chunking
│   │   ├── retrieval.py     TF-IDF, BM25 (own implementation), optional dense embeddings
│   │   ├── llm.py           OpenAI-compatible LLM call + fallback when no key / API down
│   │   ├── store.py         documents, chunks, history (JSON persistence)
│   │   └── routes.py        /api endpoints
│   ├── tests/               15 pytest tests (chunking, retrieval, API, LLM mock, PDF)
│   ├── run.py  requirements.txt  .env.example
├── frontend/                React + Vite single-page app
│   └── src/ (App.jsx, api.js, components/DocumentPanel, ChatPanel, Message, styles.css)
└── experiments/             run_experiment.py - chunk size x retrieval study for the paper
```

## Architecture

```
Upload -> extract text per page -> chunk (size/overlap) -> index (BM25/TF-IDF/dense)
Question -> rank chunks -> top-k passages -> LLM (cites [1],[2]) -> answer + sources
```

## Run it

**Backend** (Python 3.10+):
```bash
cd backend
python -m venv venv
venv\Scripts\activate            # Windows   (Linux/macOS: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env           # Linux/macOS: cp .env.example .env
python run.py                    # http://127.0.0.1:8000
```
**Frontend** (Node 18+), in a second terminal:
```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173
```
Open http://localhost:5173, upload a document, ask a question.

**LLM (optional):** put a key in `backend/.env` (`LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`).
Any OpenAI-compatible provider works (OpenAI, Groq, OpenRouter...). Without a key the app
still works and shows the best-matching passage.

**Tests:** `cd backend && python -m pytest -q`

## API

| Method | Path | Purpose |
|---|---|---|
| GET | /api/health | status, retriever, whether an LLM is configured |
| GET | /api/documents | list documents |
| POST | /api/documents | upload (multipart field `file`, .pdf/.txt, max 10 MB) |
| DELETE | /api/documents/{id} | remove a document |
| POST | /api/ask | `{"question": "...", "top_k": 4}` -> answer, sources, latency |
| GET | /api/history | last 50 questions |

## Experiment for the research paper

```bash
cd experiments
pip install scikit-learn pypdf rank_bm25 sentence-transformers
# put your PDFs in docs/, write >= 30 questions in questions.csv (see questions_template.csv)
python run_experiment.py          # writes results.csv -> fill Table II of the paper
```

## Known limitations
- Scanned (image-only) PDFs have no extractable text and need OCR.
- Storage is a JSON file: fine for a demo, use a database + vector store (FAISS/Chroma) for scale.
- No user accounts; all uploaded documents are visible to everyone using the instance.
