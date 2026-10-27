"""Measure how CodeSentry's analysis time grows with the size of a class.

A batch of n files has n(n-1)/2 pairs. The pipeline prepares every file once (tokens,
fingerprints, syntax skeleton) and then compares prepared files pairwise, so the per-file work
grows linearly and only the cheap comparison step grows with the number of pairs. This script
times analyze_batch on growing batches drawn from dataset/generated and writes
evaluation/results/benchmark.json and benchmark.md.

Run from the project root:  .venv\\Scripts\\python.exe evaluation\\benchmark.py
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine import EngineConfig, SourceFile, analyze_batch  # noqa: E402

SIZES = (10, 20, 40, 60, 90)


def load(language: str, ext: str) -> list[SourceFile]:
    paths = sorted((ROOT / "dataset" / "generated" / language).glob(f"*/*.{ext}"))
    return [SourceFile(id=i + 1, name=f"{p.parent.name}/{p.name}", language=language,
                       text=p.read_text(encoding="utf-8")) for i, p in enumerate(paths)]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    config = EngineConfig()
    rows = []
    for language, ext in (("python", "py"), ("c", "c")):
        files = load(language, ext)
        for n in SIZES:
            if n > len(files):
                continue
            batch = files[:n]
            start = time.perf_counter()
            result = analyze_batch(batch, config)
            seconds = time.perf_counter() - start
            pairs = len(result["pairs"])
            rows.append({"language": language, "files": n, "pairs": pairs,
                         "seconds": round(seconds, 2),
                         "ms_per_pair": round(seconds * 1000 / max(1, pairs), 2),
                         "lines": sum(len(f.text.splitlines()) for f in batch)})
            print(f"{language:6s} {n:3d} files  {pairs:5d} pairs  {seconds:6.2f} s  "
                  f"{rows[-1]['ms_per_pair']:5.2f} ms/pair")
    out = ROOT / "evaluation" / "results"
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (out / "benchmark.json").write_text(json.dumps({"generated_at": stamp, "rows": rows}, indent=2),
                                        encoding="utf-8")
    lines = ["# CodeSentry - scalability benchmark", "",
             f"Generated {stamp} by `evaluation/benchmark.py` on this machine (single process, default settings).", "",
             "| Language | Files | Lines of code | Pairs compared | Total time (s) | ms per pair |",
             "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['language']} | {r['files']} | {r['lines']} | {r['pairs']} | {r['seconds']:.2f} | "
                     f"{r['ms_per_pair']:.2f} |")
    (out / "benchmark.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
