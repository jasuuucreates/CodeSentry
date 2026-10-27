"""Start the CodeSentry web application.

    python run_server.py                 # http://127.0.0.1:5000, opens your browser
    python run_server.py --port 8080     # another port
    python run_server.py --no-browser    # do not open a browser window

The server listens on 127.0.0.1 only (this computer), serves the REST API under /api and the
built React interface from frontend/dist. Stop it with Ctrl+C.
"""
from __future__ import annotations

import argparse
import sys
import threading
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app import create_app  # noqa: E402

HOST = "127.0.0.1"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the CodeSentry plagiarism detector web app.")
    parser.add_argument("--port", type=int, default=5000, help="port to listen on (default 5000)")
    parser.add_argument("--no-browser", action="store_true", help="do not open the browser automatically")
    args = parser.parse_args(argv)

    app = create_app()
    url = f"http://{HOST}:{args.port}/"
    if not (Path(app.config["FRONTEND_DIST"]) / "index.html").is_file():
        print("Note: the web interface is not built yet. Run: cd frontend && npm install && npm run build")

    print(f"CodeSentry is running at {url}  (press Ctrl+C to stop)")
    if not args.no_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    app.run(host=HOST, port=args.port, debug=False, use_reloader=False, threaded=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
