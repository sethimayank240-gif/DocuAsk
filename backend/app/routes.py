"""REST API."""
import time

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from .ingestion import IngestionError, extract_pages
from .llm import generate_answer

api = Blueprint("api", __name__, url_prefix="/api")


def _store():
    return current_app.extensions["store"]


def _cfg():
    return current_app.config["APP_CONFIG"]


@api.get("/health")
def health():
    cfg = _cfg()
    return {"status": "ok", "retriever": cfg.RETRIEVER, "llm_configured": bool(cfg.LLM_API_KEY)}


@api.get("/documents")
def list_documents():
    return jsonify(_store().list_documents())


@api.post("/documents")
def upload_document():
    file = request.files.get("file")
    if file is None or not file.filename:
        return {"error": "Attach a file in the 'file' field."}, 400
    name = secure_filename(file.filename)
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in _cfg().ALLOWED_EXTENSIONS:
        return {"error": "Only .pdf and .txt files are allowed."}, 400
    try:
        pages = extract_pages(name, file.read())
        doc = _store().add_document(name, pages)
    except (IngestionError, ValueError) as exc:
        return {"error": str(exc)}, 422
    return doc, 201


@api.delete("/documents/<doc_id>")
def delete_document(doc_id):
    if not _store().delete_document(doc_id):
        return {"error": "Document not found."}, 404
    return "", 204


@api.post("/ask")
def ask():
    body = request.get_json(silent=True) or {}
    question = str(body.get("question", "")).strip()
    if not question:
        return {"error": "Question is required."}, 400
    if len(question) > 1000:
        return {"error": "Question is too long (max 1000 characters)."}, 400
    cfg = _cfg()
    try:
        k = max(1, min(int(body.get("top_k", cfg.TOP_K)), 10))
    except (TypeError, ValueError):
        return {"error": "top_k must be an integer."}, 400
    start = time.perf_counter()
    sources = _store().search(question, k)
    result = generate_answer(question, sources, cfg)
    entry = {
        "question": question,
        "answer": result["answer"],
        "mode": result["mode"],
        "sources": [{"doc_name": s["doc_name"], "page": s["page"], "score": s["score"],
                     "text": s["text"]} for s in sources],
        "latency_ms": int((time.perf_counter() - start) * 1000),
        "asked_at": int(time.time()),
    }
    _store().add_history(entry)
    return entry


@api.get("/history")
def history():
    return jsonify(_store().history[::-1])


@api.delete("/history")
def clear_history():
    _store().clear_history()
    return "", 204


@api.get("/suggestions")
def suggestions():
    return jsonify(_store().suggestions())