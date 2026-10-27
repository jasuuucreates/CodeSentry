"""REST API of CodeSentry: the ``api`` blueprint, mounted under ``/api`` by ``create_app``.

Every route returns JSON. Every error is ``{"error": "<message>"}`` with a matching HTTP status
(400 bad input, 404 not found, 413 too large, 500 unexpected), so the frontend can always show the
server's own explanation. See docs/ARCHITECTURE_CONTRACT.md, section 7.
"""
from __future__ import annotations

import io
import json
import posixpath
import zipfile
from pathlib import Path, PurePosixPath

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import or_, select

from engine import (
    SUPPORTED_LANGUAGES,
    EngineConfig,
    EngineError,
    SourceFile,
    __version__,
    analyze_batch,
    detect_language,
    explain,
)

from .db import Database, PairScore, Run, Submission
from .ml import annotate

api = Blueprint("api", __name__)

DEMO_RUN_NAME = "Demo — Assignment 3: Student Grade Statistics"
SUPPORTED_SUFFIXES = (".py", ".c", ".h")
# Settings a user may change per run (contract: k, w, w_token, w_structure).
RUN_SETTING_KEYS = ("k", "w", "w_token", "w_structure")


class ApiError(Exception):
    """Raised inside a route to return ``{"error": message}`` with the given status code."""

    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


@api.errorhandler(ApiError)
def _handle_api_error(exc: ApiError):
    return jsonify({"error": exc.message}), exc.status


def _db() -> Database:
    return current_app.extensions["codesentry_db"]


def _base_config() -> EngineConfig:
    """Default settings for new runs: the trained configuration if one was loaded, else built-in."""
    base = current_app.extensions.get("codesentry_base_config")
    return base["config"] if base else EngineConfig()


# ---------------------------------------------------------------------------------------------
# Upload handling
# ---------------------------------------------------------------------------------------------

def _decode(data: bytes, name: str) -> str:
    """Bytes of an uploaded file -> text with ``\\n`` line endings."""
    if b"\x00" in data:
        raise ApiError(f"{name} is not a text source file (it contains binary data).")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Old Windows editors save in cp1252; latin-1 accepts every byte as a last resort.
        try:
            text = data.decode("cp1252")
        except UnicodeDecodeError:
            text = data.decode("latin-1")
    # Normalising line endings keeps line numbers identical and the code view consistent.
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _limit_bytes(name: str, size: int) -> None:
    limit = current_app.config["MAX_FILE_BYTES"]
    if size > limit:
        raise ApiError(
            f"{name} is too large ({size / 1_000_000:.1f} MB). "
            f"Each file may be at most {limit / 1_000_000:.1f} MB.",
            413,
        )


def _unique_name(name: str, taken: set[str]) -> str:
    """``name`` if unused, otherwise ``stem_2.ext``, ``stem_3.ext`` ..."""
    if name not in taken:
        taken.add(name)
        return name
    stem, dot, ext = name.rpartition(".")
    if not dot:
        stem, ext = name, ""
    counter = 2
    while True:
        candidate = f"{stem}_{counter}.{ext}" if ext else f"{stem}_{counter}"
        if candidate not in taken:
            taken.add(candidate)
            return candidate
        counter += 1


def _zip_members(data: bytes, zip_name: str) -> list[tuple[str, bytes]]:
    """Supported source files inside an uploaded .zip as ``(name, bytes)`` pairs.

    Directories, ``__MACOSX/`` metadata, hidden files and unsupported extensions are skipped.
    A member whose path tries to leave the archive (``..`` or an absolute path) rejects the upload.
    """
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise ApiError(f"{zip_name} is not a valid .zip archive.") from None

    max_files = current_app.config["MAX_FILES"]
    picked: list[tuple[str, zipfile.ZipInfo]] = []
    with archive:
        for info in archive.infolist():
            raw = info.filename.replace("\\", "/")
            if info.is_dir() or raw.endswith("/"):
                continue
            if raw.startswith("/") or (len(raw) > 1 and raw[1] == ":"):
                raise ApiError(f"{zip_name} contains an unsafe absolute path: {info.filename}")
            parts = [part for part in raw.split("/") if part not in ("", ".")]
            if any(part == ".." for part in parts):
                raise ApiError(f"{zip_name} contains an unsafe path: {info.filename}")
            if not parts or parts[0] == "__MACOSX" or any(p.startswith(".") for p in parts):
                continue
            if detect_language(parts[-1]) is None:
                continue
            _limit_bytes(f"{zip_name}: {'/'.join(parts)}", info.file_size)
            picked.append(("/".join(parts), info))
            if len(picked) > max_files:
                raise ApiError(f"{zip_name} contains more than {max_files} source files.")

        # Archives usually wrap everything in one top-level folder (e.g. "assignment3/");
        # dropping it keeps the names short while sub-folders (one per student) stay visible.
        if picked and all("/" in name for name, _ in picked):
            first = {name.split("/", 1)[0] for name, _ in picked}
            if len(first) == 1:
                picked = [(name.split("/", 1)[1], info) for name, info in picked]

        members: list[tuple[str, bytes]] = []
        for name, info in picked:
            content = archive.read(info)
            _limit_bytes(f"{zip_name}: {name}", len(content))
            members.append((name, content))
    return members


def _collect_uploads() -> list[tuple[str, str, str]]:
    """Validate the multipart ``files`` field; returns ``(name, language, text)`` triples."""
    uploads = [f for f in request.files.getlist("files") if f and f.filename]
    if not uploads:
        raise ApiError("No files were uploaded. Choose at least two .py, .c or .h files (or a .zip).")

    max_files = current_app.config["MAX_FILES"]
    collected: list[tuple[str, bytes]] = []
    for upload in uploads:
        # Browsers send a bare file name; strip any folder part just in case.
        name = posixpath.basename(upload.filename.replace("\\", "/")) or "upload"
        data = upload.read()
        if name.lower().endswith(".zip"):
            # The archive itself is bounded by MAX_CONTENT_LENGTH; each member by MAX_FILE_BYTES.
            collected.extend(_zip_members(data, name))
        elif detect_language(name) is not None:
            _limit_bytes(name, len(data))
            collected.append((name, data))
        else:
            suffix = PurePosixPath(name).suffix or "(no extension)"
            raise ApiError(
                f"Unsupported file type {suffix} for {name}. "
                "Upload Python (.py) or C (.c, .h) source files, or a .zip containing them."
            )
        if len(collected) > max_files:
            raise ApiError(f"Too many files: at most {max_files} source files per analysis.")

    if len(collected) < 2:
        found = "no supported source file" if not collected else "only 1 supported source file"
        raise ApiError(
            f"An analysis needs at least 2 source files (.py, .c or .h); the upload contained {found}."
        )

    taken: set[str] = set()
    files: list[tuple[str, str, str]] = []
    for name, data in collected:
        text = _decode(data, name)
        files.append((_unique_name(name, taken), detect_language(name), text))
    return files


# ---------------------------------------------------------------------------------------------
# Storing and reading runs
# ---------------------------------------------------------------------------------------------

def _create_run(name: str, files: list[tuple[str, str, str]], config: EngineConfig) -> dict:
    """Analyze a batch and store it; returns the RunSummary of the new run."""
    with _db().session() as session, session.begin():
        run = Run(name=name, config_json=json.dumps(config.to_dict()))
        session.add(run)
        submissions = [
            Submission(run=run, name=n, language=lang, source_text=text, line_count=len(text.splitlines()))
            for n, lang, text in files
        ]
        session.add_all(submissions)
        session.flush()  # assigns database ids, which become the file ids of the analysis

        sources = [SourceFile(id=s.id, name=s.name, language=s.language, text=s.source_text)
                   for s in submissions]
        result = analyze_batch(sources, config)

        by_id = {s.id: s for s in submissions}
        for entry in result["files"]:
            submission = by_id[entry["id"]]
            submission.line_count = entry["lines"]
            submission.token_count = entry["tokens"]
            submission.warnings_json = json.dumps(entry["warnings"])

        session.add_all([
            PairScore(
                run=run,
                a_submission_id=pair["a_id"],
                b_submission_id=pair["b_id"],
                fused=pair["scores"]["fused"],
                token=pair["scores"]["token"],
                structure=pair["scores"]["structure"],
                text_baseline=pair["scores"]["text_baseline"],
                tfidf_baseline=pair["scores"]["tfidf_baseline"],
                verdict=pair["verdict"],
                result_json=json.dumps(pair),
            )
            for pair in result["pairs"]
        ])
        run.summary_json = json.dumps(result["summary"])
        run.config_json = json.dumps(result["config"])
        run.elapsed_ms = int(result["summary"].get("elapsed_ms", 0))
        session.flush()
        return run.to_summary()


def _get_run_or_404(session, run_id: int) -> Run:
    run = session.get(Run, run_id)
    if run is None:
        raise ApiError(f"Analysis run {run_id} was not found. It may have been deleted.", 404)
    return run


def _swap_pair(pair: dict) -> dict:
    """The same PairResult seen from the other file: every a_* and b_* field exchanged."""
    swapped = dict(pair)
    swapped["a_id"], swapped["b_id"] = pair["b_id"], pair["a_id"]
    swapped["a_name"], swapped["b_name"] = pair["b_name"], pair["a_name"]
    swapped["matches"] = sorted(
        (
            {**m, "a_start": m["b_start"], "a_end": m["b_end"], "b_start": m["a_start"], "b_end": m["a_end"]}
            for m in pair.get("matches", [])
        ),
        key=lambda m: (m["a_start"], m["b_start"]),
    )
    stats = dict(pair.get("stats", {}))
    for key in ("tokens", "fingerprints", "nodes"):
        a_key, b_key = f"a_{key}", f"b_{key}"
        if a_key in stats or b_key in stats:
            stats[a_key], stats[b_key] = pair.get("stats", {}).get(b_key), pair.get("stats", {}).get(a_key)
    swapped["stats"] = stats
    return swapped


# ---------------------------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------------------------

@api.get("/health")
def health():
    return jsonify({"status": "ok", "version": __version__, "languages": list(SUPPORTED_LANGUAGES)})


@api.get("/config/defaults")
def config_defaults():
    base = current_app.extensions.get("codesentry_base_config") or {"config": EngineConfig(), "trained": False}
    body = base["config"].to_dict()
    body["trained"] = bool(base.get("trained"))
    if base.get("meta") is not None:
        body["meta"] = base["meta"]
    return jsonify(body)


@api.post("/runs")
def create_run():
    files = _collect_uploads()
    settings = {key: request.form.get(key) for key in RUN_SETTING_KEYS if request.form.get(key) not in (None, "")}
    try:
        # The user's fields override the default (possibly trained) settings; the rest are kept.
        config = EngineConfig.from_dict({**_base_config().to_dict(), **settings})
    except EngineError as exc:
        raise ApiError(f"Invalid setting: {exc}") from None

    name = (request.form.get("name") or "").strip()
    if not name:
        name = f"Analysis of {len(files)} files"
    summary = _create_run(name[:200], files, config)
    return jsonify(summary), 201


@api.post("/runs/demo")
def create_demo_run():
    folder = Path(current_app.config["DATASET_DIR"]) / "demo_batch"
    paths = sorted(p for p in folder.glob("*") if p.is_file() and detect_language(p.name)) if folder.is_dir() else []
    if len(paths) < 2:
        raise ApiError(
            "The demo batch is not available: dataset/demo_batch/ is missing. "
            "Generate it with: python dataset/build_dataset.py",
            404,
        )
    files = [(p.name, detect_language(p.name), _decode(p.read_bytes(), p.name)) for p in paths]
    summary = _create_run(DEMO_RUN_NAME, files, _base_config())
    return jsonify(summary), 201


@api.get("/runs")
def list_runs():
    with _db().session() as session:
        runs = session.scalars(select(Run).order_by(Run.created_at.desc(), Run.id.desc())).all()
        return jsonify([run.to_summary() for run in runs])


@api.get("/runs/<int:run_id>")
def get_run(run_id: int):
    with _db().session() as session:
        run = _get_run_or_404(session, run_id)
        submissions = list(run.submissions)
        model = current_app.extensions.get("codesentry_model")
        pairs = [annotate(model, ps.result) for ps in run.pair_scores]
        pairs.sort(key=lambda p: p["scores"]["fused"], reverse=True)  # stable: keeps engine order on ties

        index = {s.id: i for i, s in enumerate(submissions)}
        matrix: list[list[float | None]] = [[None] * len(submissions) for _ in submissions]
        for i in range(len(submissions)):
            matrix[i][i] = 1.0
        for pair in pairs:
            i, j = index.get(pair["a_id"]), index.get(pair["b_id"])
            if i is not None and j is not None:
                matrix[i][j] = matrix[j][i] = pair["scores"]["fused"]

        body = run.to_summary()
        body.update({
            "files": [s.to_file_dict() for s in submissions],
            "matrix": matrix,
            "pairs": pairs,
            "config": run.config,
        })
        return jsonify(body)


@api.get("/runs/<int:run_id>/pairs/<int:a_id>/<int:b_id>")
def get_pair(run_id: int, a_id: int, b_id: int):
    with _db().session() as session:
        _get_run_or_404(session, run_id)
        subs = {
            s.id: s
            for s in session.scalars(
                select(Submission).where(Submission.run_id == run_id, Submission.id.in_((a_id, b_id)))
            )
        }
        for file_id in (a_id, b_id):
            if file_id not in subs:
                raise ApiError(f"File {file_id} is not part of analysis run {run_id}.", 404)
        if a_id == b_id:
            raise ApiError("A file cannot be compared with itself; choose two different files.", 400)

        row = session.scalars(
            select(PairScore).where(
                PairScore.run_id == run_id,
                or_(
                    (PairScore.a_submission_id == a_id) & (PairScore.b_submission_id == b_id),
                    (PairScore.a_submission_id == b_id) & (PairScore.b_submission_id == a_id),
                ),
            )
        ).first()
        if row is None:
            raise ApiError(
                f"{subs[a_id].name} and {subs[b_id].name} were not compared "
                "(they are in different languages, or one of them could not be parsed).",
                404,
            )
        pair = annotate(current_app.extensions.get("codesentry_model"), row.result)
        if pair["a_id"] != a_id:
            pair = _swap_pair(pair)
        pair["a_source"] = subs[a_id].source_text
        pair["b_source"] = subs[b_id].source_text
        return jsonify(pair)


@api.delete("/runs/<int:run_id>")
def delete_run(run_id: int):
    with _db().session() as session, session.begin():
        run = _get_run_or_404(session, run_id)
        session.delete(run)
    return "", 204


@api.post("/explain")
def explain_snippets():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ApiError('Send a JSON object: {"code_a": "...", "code_b": "...", "language": "python"}.')
    code_a, code_b, language = body.get("code_a"), body.get("code_b"), body.get("language", "python")
    if not isinstance(code_a, str) or not isinstance(code_b, str):
        raise ApiError("code_a and code_b must both be strings of source code.")
    if not code_a.strip() or not code_b.strip():
        raise ApiError("Both snippets must contain some code.")
    if language not in SUPPORTED_LANGUAGES:
        raise ApiError(f"Unsupported language {language!r}; choose 'python' or 'c'.")
    limit = current_app.config["MAX_FILE_BYTES"]
    if len(code_a.encode("utf-8")) > limit or len(code_b.encode("utf-8")) > limit:
        raise ApiError(f"Each snippet may be at most {limit / 1_000_000:.1f} MB.", 413)
    code_a = code_a.replace("\r\n", "\n").replace("\r", "\n")
    code_b = code_b.replace("\r\n", "\n").replace("\r", "\n")
    try:
        # Same settings as a new run, so the walkthrough matches the weights and thresholds
        # that GET /api/config/defaults reports.
        result = explain(code_a, code_b, language, _base_config())
    except EngineError as exc:
        raise ApiError(str(exc)) from None
    return jsonify(result)


@api.get("/evaluation")
def evaluation():
    path = Path(current_app.config["EVALUATION_FILE"])
    if not path.is_file():
        raise ApiError(
            "No evaluation results yet. Generate them with: python evaluation/evaluate.py", 404
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ApiError(f"The evaluation results file could not be read: {exc}", 500) from None
    return jsonify(data)
