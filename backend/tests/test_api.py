import io

import pytest

from app import create_app
from app.config import Config


@pytest.fixture
def client(tmp_path):
    class TestConfig(Config):
        DATA_DIR = tmp_path
        LLM_API_KEY = ""          # force the no-LLM fallback so tests never hit the network
        RETRIEVER = "bm25"
        CHUNK_SIZE = 40
        CHUNK_OVERLAP = 5
    return create_app(TestConfig).test_client()


def upload(client, name, content):
    return client.post("/api/documents", data={"file": (io.BytesIO(content), name)},
                       content_type="multipart/form-data")


NOTES = (b"Photosynthesis converts light into chemical energy in chloroplasts. " * 3 +
         b"The capital of France is Paris and it hosts the Eiffel Tower. " * 3)


def test_health(client):
    assert client.get("/api/health").json["status"] == "ok"


def test_upload_list_ask_delete_flow(client):
    r = upload(client, "notes.txt", NOTES)
    assert r.status_code == 201 and r.json["chunks"] >= 1
    doc_id = r.json["id"]
    assert len(client.get("/api/documents").json) == 1

    a = client.post("/api/ask", json={"question": "What is the capital of France?"})
    assert a.status_code == 200
    assert a.json["sources"] and "Paris" in a.json["sources"][0]["text"]
    assert a.json["sources"][0]["doc_name"] == "notes.txt"
    assert len(client.get("/api/history").json) == 1

    assert client.delete(f"/api/documents/{doc_id}").status_code == 204
    assert client.delete(f"/api/documents/{doc_id}").status_code == 404
    again = client.post("/api/ask", json={"question": "What is the capital of France?"})
    assert again.json["mode"] == "no_match"


def test_rejects_bad_input(client):
    assert upload(client, "virus.exe", b"x").status_code == 400
    assert upload(client, "empty.txt", b"   ").status_code == 422
    assert upload(client, "bad.pdf", b"not a pdf").status_code == 422
    assert client.post("/api/ask", json={"question": ""}).status_code == 400
    assert client.post("/api/ask", json={"question": "x" * 2000}).status_code == 400
    assert client.post("/api/ask", json={"question": "hi", "top_k": "abc"}).status_code == 400
    assert client.post("/api/documents", data={}).status_code == 400


def test_path_traversal_filename_is_sanitised(client):
    r = upload(client, "../../etc/passwd.txt", b"some harmless text here")
    assert r.status_code == 201 and "/" not in r.json["name"]


def test_persistence_survives_restart(client, tmp_path):
    upload(client, "notes.txt", NOTES)
    class C(Config):
        DATA_DIR = tmp_path; LLM_API_KEY = ""; RETRIEVER = "bm25"
    c2 = create_app(C).test_client()
    assert len(c2.get("/api/documents").json) == 1


def test_suggestions_and_clear_history(client):
    assert client.get("/api/suggestions").json == []
    upload(client, "notes.txt", NOTES)
    sug = client.get("/api/suggestions").json
    assert 1 <= len(sug) <= 4 and all(q.endswith("?") for q in sug)
    client.post("/api/ask", json={"question": "What is the capital of France?"})
    assert len(client.get("/api/history").json) == 1
    assert client.delete("/api/history").status_code == 204
    assert client.get("/api/history").json == []