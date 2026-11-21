from flask import Flask

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
