"""Language detection for uploaded files.

CodeSentry supports exactly two languages. A file's language decides which tokenizer and which
syntax-tree builder the pipeline uses, and only files of the same language are ever compared.
"""
from __future__ import annotations

import os

# File extension (lower case, with the dot) -> language name used everywhere in the engine.
SUPPORTED_EXTENSIONS: dict[str, str] = {".py": "python", ".c": "c", ".h": "c"}


def detect_language(filename: str, text: str | None = None) -> str | None:
    """Return ``'python'``, ``'c'`` or ``None`` for a file name such as ``"student_01.PY"``.

    Detection uses the extension only, compared case-insensitively. That keeps it predictable
    and identical to the rule the upload form and the zip extractor use to accept files;
    guessing from the content would be unreliable (a short C header and a short Python module
    can look alike). `text` is accepted so callers can pass what they have without knowing
    how detection works, but it does not influence the answer.
    """
    extension = os.path.splitext(filename)[1].lower()
    return SUPPORTED_EXTENSIONS.get(extension)
