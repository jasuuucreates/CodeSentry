"""Default settings of the CodeSentry web server.

Every value here can be replaced by passing a dictionary to ``create_app(test_config)``. The tests
use that to point the database at a temporary file and the dataset or frontend folders at
temporary directories, so running the test suite never touches the real data.
See docs/ARCHITECTURE_CONTRACT.md, section 7.
"""
from __future__ import annotations

from pathlib import Path

# backend/config.py -> backend/ -> project root. Computing it from this file's location (instead
# of the current working directory) means the server finds its folders no matter where it is
# started from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class DefaultConfig:
    """Settings loaded into ``app.config`` before any test or user overrides."""

    # SQLite keeps the whole database in one file next to the backend code: nothing to install,
    # and it works offline in a viva room. as_posix() gives forward slashes, which SQLAlchemy
    # accepts on Windows and which avoid backslash-escaping surprises in the URL.
    DATABASE_URL = f"sqlite:///{(PROJECT_ROOT / 'backend' / 'codesentry.db').as_posix()}"

    # Upload limits. MAX_FILES bounds the work (n files mean n(n-1)/2 comparisons),
    # MAX_FILE_BYTES rejects anything far larger than a student submission, and
    # MAX_CONTENT_LENGTH is Flask's own cap on the size of a whole request body.
    MAX_FILES = 200
    MAX_FILE_BYTES = 2_000_000
    MAX_CONTENT_LENGTH = 60_000_000

    # Where the built React app, the dataset and the evaluation results live.
    FRONTEND_DIST = str(PROJECT_ROOT / "frontend" / "dist")
    DATASET_DIR = str(PROJECT_ROOT / "dataset")
    EVALUATION_FILE = str(PROJECT_ROOT / "evaluation" / "results" / "evaluation.json")

    # Optional settings learned from the labelled dataset (fusion weights, verdict thresholds ...).
    # When this file exists it replaces the built-in EngineConfig defaults for new runs; the
    # values a user types on the New Analysis page still override it.
    TRAINED_CONFIG_FILE = str(PROJECT_ROOT / "engine" / "trained_config.json")

    # Optional logistic-regression model (training/train_model.py). When it exists, every pair in
    # the run and pair responses also carries scores.ml_probability (see backend/ml.py).
    TRAINED_MODEL_FILE = str(PROJECT_ROOT / "engine" / "trained_model.json")

    # Outputs of training/train_model.py shown on the Model Training page (GET /api/training).
    TRAINING_REPORT_FILE = str(PROJECT_ROOT / "training" / "results" / "training_report.json")
    TRAINING_FEATURES_FILE = str(PROJECT_ROOT / "training" / "results" / "features.csv")
