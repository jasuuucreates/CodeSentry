"""Flask application factory of CodeSentry.

``create_app()`` builds the whole web server:

* the REST API (``backend/routes.py``) under ``/api``, with CORS enabled for ``/api/*``;
* the SQLite database (``backend/db.py``);
* the built React single-page app from ``frontend/dist``: any other GET returns the requested
  static file if it exists, otherwise ``index.html`` so React Router can show the right page.

See docs/ARCHITECTURE_CONTRACT.md, section 7.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
# The engine package lives next to the backend; make "import engine" work no matter which
# directory the server was started from.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, jsonify, request, send_from_directory  # noqa: E402
from flask_cors import CORS  # noqa: E402
from werkzeug.exceptions import HTTPException, NotFound  # noqa: E402

from engine import EngineConfig  # noqa: E402

from .config import DefaultConfig  # noqa: E402
from .db import Database  # noqa: E402
from .ml import load_model  # noqa: E402
from .routes import api  # noqa: E402

log = logging.getLogger("codesentry")


def load_base_config(path: str | None) -> tuple[EngineConfig, bool, dict | None]:
    """The default EngineConfig for new runs: ``(config, trained, meta)``.

    If ``path`` names an existing JSON file (written by the training script), its settings are
    used; the optional ``"meta"`` object describes how they were obtained. A missing file means
    the built-in defaults; an unreadable or invalid file also falls back to them, with a warning.
    """
    if not path or not Path(path).is_file():
        return EngineConfig(), False, None
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("the file must contain a JSON object")
        config = EngineConfig.from_dict({k: v for k, v in data.items() if k != "meta"})
        total = config.w_token + config.w_structure
        if abs(total - 1.0) > 1e-9:
            # Fusion normalizes the weights anyway; storing them normalized lets the interface
            # show them as the percentages that are really applied.
            config.w_token = round(config.w_token / total, 6)
            config.w_structure = round(1.0 - config.w_token, 6)
        meta = data.get("meta")
        return config, True, meta if isinstance(meta, dict) else None
    except (OSError, ValueError, TypeError) as exc:  # EngineError is a ValueError
        log.warning("Ignoring trained configuration %s (%s); using the built-in defaults.", path, exc)
        return EngineConfig(), False, None

NOT_BUILT_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>CodeSentry</title>
<style>body{font-family:system-ui,sans-serif;max-width:640px;margin:64px auto;padding:0 16px;color:#1e293b}
code,pre{background:#f1f5f9;border-radius:6px}pre{padding:12px}</style></head>
<body><h1>CodeSentry</h1>
<p>The API is running, but the web interface has not been built yet.</p>
<p>Build it once (Node.js 20+ required):</p>
<pre>cd frontend
npm install
npm run build</pre>
<p>Then reload this page. The API itself is available at <a href="/api/health"><code>/api/health</code></a>.</p>
</body></html>
"""


def _is_api_request() -> bool:
    return request.path == "/api" or request.path.startswith("/api/")


def create_app(test_config: dict | None = None) -> Flask:
    """Create and configure the CodeSentry Flask app.

    ``test_config`` overrides any key of :class:`backend.config.DefaultConfig`, e.g.
    ``{"TESTING": True, "DATABASE_URL": "sqlite:///:memory:"}``.
    """
    # static_folder=None: the SPA route below serves frontend/dist itself.
    app = Flask(__name__, static_folder=None)
    app.config.from_object(DefaultConfig)
    if test_config:
        app.config.update(test_config)
    app.json.sort_keys = False  # keep the field order of the contract in responses

    app.extensions["codesentry_db"] = Database(app.config["DATABASE_URL"])
    base, trained, meta = load_base_config(app.config.get("TRAINED_CONFIG_FILE"))
    app.extensions["codesentry_base_config"] = {"config": base, "trained": trained, "meta": meta}
    app.extensions["codesentry_model"] = load_model(app.config.get("TRAINED_MODEL_FILE"))

    CORS(app, resources={r"/api/*": {"origins": "*"}})
    app.register_blueprint(api, url_prefix="/api")

    @app.errorhandler(HTTPException)
    def _http_error(exc: HTTPException):
        if not _is_api_request():
            return exc
        message = exc.description or exc.name
        if exc.code == 413:
            limit = app.config.get("MAX_CONTENT_LENGTH") or 0
            message = (f"The upload is too large. The whole request may be at most "
                       f"{limit / 1_000_000:g} MB.")
        elif exc.code == 404:
            message = f"No API endpoint {request.method} {request.path}."
        elif exc.code == 405:
            message = f"Method {request.method} is not allowed for {request.path}."
        return jsonify({"error": message}), exc.code

    @app.errorhandler(Exception)
    def _unexpected_error(exc: Exception):
        if isinstance(exc, HTTPException):  # pragma: no cover - handled above
            return _http_error(exc)
        log.exception("Unhandled error while serving %s %s", request.method, request.path)
        if app.config.get("TESTING") and app.config.get("PROPAGATE_EXCEPTIONS"):
            raise exc
        return jsonify({"error": f"Internal server error: {exc.__class__.__name__}: {exc}"}), 500

    dist = Path(app.config["FRONTEND_DIST"])

    @app.get("/", defaults={"path": ""})
    @app.get("/<path:path>")
    def spa(path: str):
        if path == "api" or path.startswith("api/"):
            raise NotFound()
        index = dist / "index.html"
        if not index.is_file():
            return NOT_BUILT_PAGE, 200, {"Content-Type": "text/html; charset=utf-8"}
        if path:
            try:
                candidate = (dist / path).resolve()
                if candidate.is_file() and candidate.is_relative_to(dist.resolve()):
                    return send_from_directory(dist, path)
            except (OSError, ValueError):
                pass
        # Any other address is a page of the React app: index.html lets React Router render it.
        response = send_from_directory(dist, "index.html", max_age=0)
        response.headers["Cache-Control"] = "no-cache"
        return response

    return app
