"""CodeSentry web backend: Flask REST API + SQLite storage + serving of the built React app.

Start it with ``python run_server.py`` from the project root, or build an app object in code::

    from backend.app import create_app
    app = create_app({"TESTING": True, "DATABASE_URL": "sqlite:///:memory:"})

See docs/ARCHITECTURE_CONTRACT.md, section 7.
"""
from .app import create_app

__all__ = ["create_app"]
