import os
from pathlib import Path

from flask import Flask, send_from_directory

from .config import Config
from .routes import api
from .store import DocumentStore


def create_app(config=Config) -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
    app.config["APP_CONFIG"] = config
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    app.extensions["store"] = DocumentStore(config)
    app.register_blueprint(api)

    # Optional: serve the built React app (used by the single-container online deployment).
    static_dir = Path(os.getenv("STATIC_DIR", "")) if os.getenv("STATIC_DIR") else None
    if static_dir and static_dir.is_dir():
        @app.route("/", defaults={"path": ""})
        @app.route("/<path:path>")
        def spa(path):
            if path and (static_dir / path).is_file():
                return send_from_directory(static_dir, path)
            return send_from_directory(static_dir, "index.html")

    @app.after_request
    def cors(resp):  # minimal CORS so the React dev server can call the API
        resp.headers["Access-Control-Allow-Origin"] = config.FRONTEND_ORIGIN
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "GET,POST,DELETE,OPTIONS"
        return resp

    @app.errorhandler(413)
    def too_large(_):
        return {"error": f"File too large (max {config.MAX_UPLOAD_MB} MB)."}, 413

    return app
