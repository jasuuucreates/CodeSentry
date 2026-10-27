# CodeSentry — Architecture Contract (binding for every build agent)

This document is the single source of truth. Several agents build different parts of the
system at the same time. Code ONLY against the interfaces written here. Do not change a
signature, JSON field name, route, or file location defined here. If you find a genuine
defect in the contract, do not silently diverge — implement the contract as written and
report the problem in your final structured output under `contract_deviations`.

Project root (all paths below are relative to it):
`D:\padhai\se lab updated\CodeSentry_Project\CodeSentry\`

---------------------------------------------------------------------------------------------

## 0. Environment facts (VERIFIED — do not re-litigate)

* Python: `.venv\Scripts\python.exe` (CPython 3.11.9). Always run Python through this venv.
* Windows **Smart App Control is enforcing** on this machine. It blocks unsigned compiled
  extensions. Verified results:
  * LOAD OK: `flask`, `flask_cors`, `sqlalchemy` (sync ORM verified on SQLite), stdlib
    `sqlite3`, `tree_sitter`, `tree_sitter_c` (real parse verified), `pytest`, `numpy`, `scipy`.
  * BLOCKED — **never import**: `sklearn` / scikit-learn, `pandas`, `greenlet`, and therefore any
    asyncio SQLAlchemy feature.
* The detection engine must be **pure Python + stdlib**, plus `tree_sitter`/`tree_sitter_c`
  for C parsing. Do NOT use numpy/scipy in the engine (keep every formula explicit and
  explainable in a viva).
* Node 24, npm 11. Frontend toolchain verified building on this machine: Vite 8, React 19,
  Tailwind CSS v4 via `@tailwindcss/vite`, `chart.js` 4, `react-chartjs-2` 5, `axios` 1,
  `react-router-dom` 7. **No other npm packages.**
* The final product must run fully OFFLINE (a viva room may have no internet): no CDNs,
  no Google Fonts, no remote images, no runtime downloads.
* Paths contain spaces (`se lab updated`). Always quote paths in shell commands.

---------------------------------------------------------------------------------------------

## 1. Folder layout and file ownership

```
CodeSentry/
  engine/
    __init__.py            (pipeline agent)
    models.py              (lexer agent)
    lang.py                (lexer agent)
    tokenizer_python.py    (lexer agent)
    tokenizer_c.py         (lexer agent)
    normalizer.py          (lexer agent)
    winnowing.py           (winnowing agent)
    structure_common.py    (structure agent)
    structure_python.py    (structure agent)
    structure_c.py         (structure agent)
    tree_similarity.py     (structure agent)
    baselines.py           (pipeline agent)
    fusion.py              (pipeline agent)
    pipeline.py            (pipeline agent)
  backend/
    __init__.py  app.py  config.py  db.py  routes.py      (backend agent)
  run_server.py            (backend agent)
  requirements.txt         (backend agent)
  frontend/                (frontend agents — see section 7)
  dataset/
    problems/pNN/...       (dataset program agents)
    demo_source/           (demo source agent)
    obfuscator.py          (obfuscator agent)
    build_dataset.py       (obfuscator agent)
    generated/             (OUTPUT of build_dataset.py — never hand-edited)
    labels.json            (OUTPUT of build_dataset.py)
    demo_batch/            (OUTPUT of build_dataset.py)
  evaluation/
    evaluate.py            (evaluation agent)
    results/               (OUTPUT of evaluate.py)
  tests/                   (tests agent)
  pytest.ini               (tests agent)
  docs/ARCHITECTURE_CONTRACT.md   (this file — read only)
```

Never create, modify or delete a file owned by another agent.

---------------------------------------------------------------------------------------------

## 2. Engine data model — `engine/models.py`

```python
from dataclasses import dataclass, field

class EngineError(ValueError): ...
class TokenizeError(EngineError): ...
class StructureError(EngineError): ...

@dataclass(frozen=True)
class Token:
    kind: str        # see section 3
    value: str       # exact source text of the token
    line: int        # 1-based
    col: int         # 0-based
    end_line: int    # 1-based
    end_col: int     # 0-based, exclusive

@dataclass
class SourceFile:
    id: int
    name: str
    language: str    # 'python' | 'c'
    text: str

@dataclass(frozen=True)
class Fingerprint:
    hash: int        # unsigned 64-bit
    start: int       # index of first normalized token of the k-gram
    end: int         # index of last normalized token of the k-gram (inclusive)
    line_start: int  # source line of token `start`
    line_end: int    # source line of token `end`

@dataclass
class Node:
    label: str
    children: list["Node"] = field(default_factory=list)
    def size(self) -> int: ...          # number of nodes in this subtree (iterative, no recursion limit issues)
    def to_dict(self, max_depth: int | None = None) -> dict: ...   # {"label":..., "children":[...]}

@dataclass
class MatchRegion:
    a_start: int     # 1-based inclusive line in file A
    a_end: int
    b_start: int     # 1-based inclusive line in file B
    b_end: int
    tokens: int      # approximate number of matched normalized tokens in the region
    def to_dict(self) -> dict: ...

@dataclass
class EngineConfig:
    k: int = 5                       # k-gram length (normalized tokens)
    w: int = 4                       # winnowing window size
    w_token: float = 0.5             # fusion weight of token score
    w_structure: float = 0.5         # fusion weight of structure score
    high_threshold: float = 0.75
    moderate_threshold: float = 0.50
    ted_node_cap: int = 200          # above this many nodes in either tree, use approximation
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, d: dict | None) -> "EngineConfig": ...   # ignores unknown keys, validates ranges, raises EngineError on invalid values
```

`PairResult` and `BatchResult` are plain dicts produced by `pipeline.py` (section 5), not dataclasses.

---------------------------------------------------------------------------------------------

## 3. Tokenizers and normalization (lexer agent)

### `engine/lang.py`
`detect_language(filename: str, text: str | None = None) -> str | None`
`.py` → `'python'`; `.c` or `.h` → `'c'`; anything else → `None` (case-insensitive extension).
`SUPPORTED_EXTENSIONS = {'.py': 'python', '.c': 'c', '.h': 'c'}`

### Raw token kinds (both tokenizers)
`'KEYWORD' 'IDENT' 'NUMBER' 'STRING' 'CHAR' 'OP' 'INDENT' 'DEDENT' 'COMMENT' 'PREPROC'`

### `engine/tokenizer_python.py`
`tokenize_python(text: str) -> list[Token]` — uses the stdlib `tokenize` module.
* NAME that is a keyword (`keyword.iskeyword`, also soft keywords `match`/`case` only when
  they behave as keywords is NOT required — treat them as IDENT) → `KEYWORD`; other NAME → `IDENT`.
* NUMBER → `NUMBER`; STRING → `STRING`; OP → `OP`; COMMENT → `COMMENT`; INDENT/DEDENT kept.
* NEWLINE, NL, ENCODING, ENDMARKER are dropped.
* Any `tokenize.TokenError` or `IndentationError`/`SyntaxError` → raise `TokenizeError` with a
  human-readable message including the line number.

### `engine/tokenizer_c.py`
`tokenize_c(text: str) -> list[Token]` — hand-written longest-match lexer (no tree-sitter here).
* `//` and `/* */` comments → `COMMENT`; a preprocessor directive line (optional leading
  whitespace then `#`, including backslash-continued lines) → one `PREPROC` token.
* String literals with escapes and prefixes (`L`, `u`, `U`, `u8`) → `STRING`; char literals → `CHAR`.
* Numbers: decimal, octal, hex (`0x`), binary (`0b`), floats with exponents, suffixes
  (`u l ul ull f` any case) → `NUMBER`.
* C11 keywords (`auto break case char const continue default do double else enum extern float
  for goto if inline int long register restrict return short signed sizeof static struct switch
  typedef union unsigned void volatile while _Bool _Complex _Imaginary`) → `KEYWORD`.
* Multi-character operators matched longest first: `>>= <<= ... -> ++ -- << >> <= >= == != && ||
  += -= *= /= %= &= |= ^= ##` then single characters → `OP`.
* An unterminated string/char/block comment → raise `TokenizeError`.

### `engine/normalizer.py`
`normalize(tokens: list[Token], language: str) -> list[Token]`
Returns a NEW list; each returned Token keeps value/line/col but its `kind` becomes the
canonical symbol:
* `IDENT` → `'ID'`, `NUMBER` → `'NUM'`, `STRING` → `'STR'`, `CHAR` → `'CHR'`
* `KEYWORD` → the keyword text itself (e.g. `'for'`), `OP` → the operator text (e.g. `'+='`)
* `INDENT` → `'INDENT'`, `DEDENT` → `'DEDENT'`
* `COMMENT` and `PREPROC` are removed.

`symbols(normalized: list[Token]) -> list[str]` returns `[t.kind for t in normalized]`.

Rationale to keep in docstrings: renaming variables cannot change the symbol stream, and
comments/formatting never reach it.

---------------------------------------------------------------------------------------------

## 4. Winnowing — `engine/winnowing.py` (winnowing agent)

Reference: Schleimer, Wilkerson & Aiken (2003), *Winnowing: Local Algorithms for Document Fingerprinting*.

```python
def kgram_hashes(symbols: list[str], k: int) -> list[int]
    # len == max(0, len(symbols) - k + 1)
    # hash of k-gram i = int.from_bytes(hashlib.blake2b("\x1f".join(symbols[i:i+k]).encode("utf-8"),
    #                                   digest_size=8).digest(), "big")

def winnow(hashes: list[int], w: int) -> list[tuple[int, int]]
    # robust winnowing: slide a window of w consecutive hashes; in each window select the
    # minimum hash; on ties select the RIGHTMOST occurrence; record (hash, position) only when
    # the selected position differs from the previously recorded one.
    # if 0 < len(hashes) < w: select the rightmost global minimum once.
    # empty input -> []

def fingerprint(tokens: list[Token], k: int, w: int) -> list[Fingerprint]
    # tokens are NORMALIZED tokens. k-gram at position p covers tokens p .. p+k-1.
    # line_start = tokens[p].line, line_end = tokens[p+k-1].end_line

def jaccard(fa: list[Fingerprint], fb: list[Fingerprint]) -> float
    # |set(A.hash) ∩ set(B.hash)| / |set(A.hash) ∪ set(B.hash)|; if the union is empty -> 0.0

def containment(fa: list[Fingerprint], fb: list[Fingerprint]) -> float
    # |∩| / min(|set A|, |set B|); if either set is empty -> 0.0

def match_regions(fa: list[Fingerprint], fb: list[Fingerprint]) -> list[MatchRegion]
    # For every hash present in both, pair each occurrence in A with each occurrence in B
    # (cap at 8 x 8 occurrences per hash to bound cost). Merge pairs into regions: two pairs
    # belong to the same region when their A line ranges overlap or are adjacent (gap <= 1 line)
    # AND their B line ranges overlap or are adjacent. Output regions sorted by (a_start, b_start),
    # with no region fully contained in another. `tokens` = number of distinct token positions
    # covered in A by the merged k-grams.
```

---------------------------------------------------------------------------------------------

## 5. Structure — structure agent

### `engine/structure_common.py`
`canonical_label(language: str, raw: str) -> str | None` — maps a raw AST node type to a
canonical label, or `None` to DROP the node (its children are promoted to the parent).
`OPERATOR_LABELS` maps C operator text to Python-style names:
`{'+':'Add','-':'Sub','*':'Mult','/':'Div','%':'Mod','<':'Lt','>':'Gt','<=':'LtE','>=':'GtE',
 '==':'Eq','!=':'NotEq','&&':'And','||':'Or','&':'BitAnd','|':'BitOr','^':'BitXor','<<':'LShift','>>':'RShift'}`

Required canonical labels (both languages map onto the same vocabulary where the concept exists):
`Program Function Class Params Param Return Assign AugAssign Loop If Else Switch Case Try With
 Break Continue Pass Call BinOp BoolOp UnaryOp Compare Index Attr Var Const Collection Dict
 Comprehension ExprStmt Import Decl Block Type Ptr Array` plus operator leaves
`Add Sub Mult Div Mod Pow FloorDiv Lt Gt LtE GtE Eq NotEq And Or Not In NotIn Is IsNot BitAnd BitOr BitXor LShift RShift USub UAdd Invert`.

**Every loop form (Python `For`, `AsyncFor`, `While`; C `for_statement`, `while_statement`,
`do_statement`) maps to `Loop`.** This is deliberate: swapping a for loop for a while loop does
not change the structural skeleton.

### `engine/structure_python.py`
`python_skeleton(text: str) -> Node` — `ast.parse`; `SyntaxError` → raise `StructureError`.
Drops expression contexts (`Load`, `Store`, `Del`) and docstrings (an `Expr` whose value is a
string `Constant` as the first statement of a module/function/class). Identifier names and
literal values are never part of any label.

### `engine/structure_c.py`
`c_skeleton(text: str) -> Node` — tree-sitter C (`Language(tree_sitter_c.language())`).
Named nodes only. `comment` and `preproc_*` nodes dropped. `binary_expression` becomes
`Compare` (`== != < > <= >=`), `BoolOp` (`&& ||`) or `BinOp` (otherwise) with an operator leaf
child from `OPERATOR_LABELS`. `assignment_expression` with a compound operator (`+=` etc.) and
`update_expression` (`i++`) become `AugAssign`. Unknown named node types keep a label derived
from their type name (CamelCase), they are not dropped. If the tree contains `ERROR` or missing
nodes, still return the tree but set `c_skeleton.last_had_errors = True` (module-level flag) —
the pipeline turns that into a warning.

### `engine/tree_similarity.py`
```python
def tree_size(node: Node) -> int
def canonical_order(node: Node) -> Node
    # Returns a NEW tree whose ROOT's children are sorted by their subtree hash (deeper levels
    # keep their original order). Definition order at the top level of a file does not change
    # what the program does, so reordering functions must not change the structural score.
def zhang_shasha(a: Node, b: Node) -> int
    # classic Zhang–Shasha tree edit distance, unit costs for insert / delete / relabel.
    # Iterative post-order numbering, keyroots, integer label ids, local-variable binding in
    # the inner loops — this is the hot path, optimize it.
def levenshtein(a: list[int], b: list[int]) -> int
    # Edit distance between two integer sequences using the Myers/Hyyrö bit-parallel algorithm
    # with Python arbitrary-precision ints (fast even for sequences of several thousand items).
def ted_similarity(a: Node, b: Node, node_cap: int = 200) -> tuple[float, str]
    # if size(a) <= node_cap and size(b) <= node_cap:
    #     sim = 1 - zhang_shasha(a,b) / max(size(a), size(b)); method = "zhang-shasha"
    # else: sim = 1 - levenshtein(preorder_label_ids(a), preorder_label_ids(b)) / max(len..);
    #       method = "preorder-sequence-approximation"
    #       (the string edit distance of pre-order traversals is a known lower bound of tree
    #        edit distance — say so in the docstring)
    # clamp to [0,1]
def subtree_hashes(node: Node) -> "collections.Counter[str]"
    # hash of a subtree = blake2b-8 hex of label + "(" + ",".join(child hashes in order) + ")"
def subtree_bag_similarity(a: Node, b: Node) -> float
    # multiset Jaccard: sum(min counts) / sum(max counts); both empty -> 0.0
def structural_similarity(a: Node, b: Node, node_cap: int = 200) -> dict
    # applies canonical_order() to both trees first, then
    # {"structure": 0.5*ted + 0.5*subtree, "ted": ted, "subtree": subtree,
    #  "method": method, "a_nodes": size(a), "b_nodes": size(b)}
```
Everything must be iterative where recursion depth could exceed ~900 (deeply nested code).

Performance requirements — measure and report the numbers:
* `zhang_shasha` on two random-but-code-shaped trees of 200 nodes each: under 1.0 s.
  Report the time at 100, 150, 200 and 300 nodes. (The orchestrator will set the default
  `ted_node_cap` from these measurements, so report them accurately.)
* `structural_similarity` on two 3000-node trees (approximation path): under 0.3 s.

---------------------------------------------------------------------------------------------

## 6. Baselines, fusion, pipeline — pipeline agent

### `engine/baselines.py`
```python
def text_similarity(a_text: str, b_text: str) -> float
    # "plain text matching" baseline: difflib.SequenceMatcher(None, a_lines, b_lines, autojunk=False).ratio()
    # where lines = text.splitlines() with NO other normalization.
WORD_RE = r"[A-Za-z_][A-Za-z0-9_]*|\d+|[^\sA-Za-z0-9_]"
def tfidf_vectors(texts: list[str]) -> list[dict[str, float]]
    # terms = WORD_RE matches lowercased (raw identifiers kept — this is the conventional baseline)
    # tf = raw count; idf = ln((1 + N) / (1 + df)) + 1  (smoothed, same formula scikit-learn uses)
    # weight = tf * idf, then L2-normalize each vector
def cosine(u: dict[str, float], v: dict[str, float]) -> float
def tfidf_cosine_matrix(texts: list[str]) -> list[list[float]]
```

### `engine/fusion.py`
```python
def fuse(token: float, structure: float | None, config: EngineConfig) -> float
    # structure None -> return token. Otherwise weighted mean with weights normalized to sum 1.
def verdict(score: float, config: EngineConfig) -> str   # "High" | "Moderate" | "Low"
```

### `engine/pipeline.py`
```python
@dataclass
class PreparedFile:
    source: SourceFile
    raw_tokens: list[Token]
    tokens: list[Token]             # normalized
    fingerprints: list[Fingerprint]
    skeleton: Node | None
    line_count: int
    warnings: list[str]

def prepare(file: SourceFile, config: EngineConfig) -> PreparedFile
    # tokenize (TokenizeError -> re-raise), normalize, fingerprint, build skeleton
    # (StructureError -> skeleton None + warning; C parse errors -> warning)

def compare_prepared(pa: PreparedFile, pb: PreparedFile, config: EngineConfig,
                     tfidf_score: float | None = None) -> dict   # PairResult

def analyze_pair(a: SourceFile, b: SourceFile, config: EngineConfig | None = None) -> dict
def analyze_batch(files: list[SourceFile], config: EngineConfig | None = None,
                  progress: "Callable[[int, int], None] | None" = None) -> dict   # BatchResult
def explain(code_a: str, code_b: str, language: str, config: EngineConfig | None = None) -> dict
```
Short-file rule: if either normalized stream is shorter than k, use
`k_eff = max(2, min(len_a, len_b))`; if a stream is shorter than 2 tokens the token score is
`1.0` when both symbol lists are equal and non-empty, else `0.0`. Record the effective k in
`stats.k_effective`.

`analyze_batch` prepares every file exactly once, computes one TF-IDF matrix per language over
that language's files in the batch, and compares every same-language pair `i < j`.
Different-language pairs are not compared (matrix cell `null`).

**PairResult** (exact keys):
```json
{
  "a_id": 1, "b_id": 2, "a_name": "student_01.py", "b_name": "student_02.py",
  "language": "python",
  "scores": {
    "token": 0.0, "containment": 0.0,
    "structure": 0.0, "ted": 0.0, "subtree": 0.0,
    "fused": 0.0,
    "text_baseline": 0.0, "tfidf_baseline": 0.0
  },
  "verdict": "High",
  "matches": [ {"a_start": 1, "a_end": 9, "b_start": 4, "b_end": 12, "tokens": 37} ],
  "stats": {
    "a_tokens": 0, "b_tokens": 0, "a_fingerprints": 0, "b_fingerprints": 0,
    "shared_fingerprints": 0, "a_nodes": 0, "b_nodes": 0,
    "k_effective": 5, "structure_method": "zhang-shasha"
  },
  "warnings": []
}
```
`structure`, `ted`, `subtree`, `a_nodes`, `b_nodes` are `null` when a skeleton is missing.
All scores are rounded to 4 decimal places.

**BatchResult** (exact keys):
```json
{
  "files": [ {"id": 1, "name": "student_01.py", "language": "python", "lines": 42, "tokens": 310, "warnings": []} ],
  "pairs": [ PairResult, ... ],                 // sorted by scores.fused descending
  "matrix": [[1.0, 0.31, null], ...],           // fused scores, same order as files; diagonal 1.0
  "summary": {"files": 3, "pairs_compared": 3, "high": 1, "moderate": 0, "low": 2,
              "max_score": 0.91, "mean_score": 0.44, "elapsed_ms": 812},
  "config": EngineConfig.to_dict()
}
```
Files that fail to tokenize are still listed (with a warning) and every pair involving them is
skipped (`null` in the matrix).

**explain()** result:
```json
{
  "language": "python",
  "a": {"raw_tokens": [{"kind": "IDENT", "value": "total", "line": 1}],
        "normalized": ["ID", "=", "NUM"],
        "kgrams": [{"index": 0, "text": "ID = NUM ...", "hash": "9f2c51ab03e4d7c1"}],
        "fingerprints": [{"hash": "9f2c51ab03e4d7c1", "position": 0, "line_start": 1, "line_end": 2}],
        "skeleton": {"label": "Program", "children": []},
        "counts": {"raw_tokens": 0, "normalized": 0, "kgrams": 0, "fingerprints": 0, "nodes": 0}},
  "b": { "...same shape..." },
  "result": PairResult
}
```
Cap the lists: raw_tokens/normalized first 80, kgrams first 12, fingerprints first 40,
skeleton depth 6. Hashes are 16-hex-digit strings. Use `a_id=1, b_id=2, a_name="Snippet A",
b_name="Snippet B"`.

### `engine/__init__.py`
Re-exports: `EngineConfig, SourceFile, EngineError, TokenizeError, StructureError,
detect_language, analyze_pair, analyze_batch, explain, SUPPORTED_LANGUAGES = ("python", "c")`,
`__version__ = "1.0.0"`.

---------------------------------------------------------------------------------------------

## 7. Backend — Flask REST API (backend agent)

* `backend/app.py`: `create_app(test_config: dict | None = None) -> Flask`. Inserts the project
  root into `sys.path`. Registers the `api` blueprint under `/api`. Enables CORS for `/api/*`.
  Serves the built SPA from `frontend/dist`: any non-`/api` GET returns the static file if it
  exists, otherwise `index.html`. If `frontend/dist` does not exist, `/` returns a small HTML
  page saying the frontend is not built and how to build it.
* `backend/config.py`: defaults `DATABASE_URL = sqlite:///<root>/backend/codesentry.db`,
  `MAX_FILES = 200`, `MAX_FILE_BYTES = 2_000_000`, `MAX_CONTENT_LENGTH = 60_000_000`.
  `test_config` may override any key (tests use `sqlite:///:memory:` or a temp file).
* `backend/db.py`: SQLAlchemy 2.x **synchronous** ORM (no asyncio).
  * `Run(id, name, created_at, config_json, summary_json, elapsed_ms)`
  * `Submission(id, run_id→Run, name, language, source_text, line_count, token_count, warnings_json)`
  * `PairScore(id, run_id→Run, a_submission_id, b_submission_id, fused, token, structure,
     text_baseline, tfidf_baseline, verdict, result_json)`
  * cascade delete from Run.
* All errors return JSON `{"error": "<message>"}` with a proper status code (400/404/413/500).

| Method | Path | Behaviour |
|---|---|---|
| GET | `/api/health` | `{"status":"ok","version":"1.0.0","languages":["python","c"]}` |
| GET | `/api/config/defaults` | `EngineConfig().to_dict()` |
| POST | `/api/runs` | multipart: `files` (repeated; `.py` `.c` `.h` or `.zip` containing them), optional `name`, `k`, `w`, `w_token`, `w_structure`. Validates, analyzes synchronously, stores, returns **201** with `RunSummary` |
| POST | `/api/runs/demo` | builds a run from `dataset/demo_batch/*` (name "Demo — Assignment 3: Student Grade Statistics"); 404 JSON error if the folder is missing; returns **201** `RunSummary` |
| GET | `/api/runs` | list of `RunSummary`, newest first |
| GET | `/api/runs/<id>` | `RunSummary` fields + `files`, `matrix`, `pairs` (each pair WITHOUT source text), `config` |
| GET | `/api/runs/<id>/pairs/<a_id>/<b_id>` | PairResult + `a_source`, `b_source`. Order-insensitive (`/2/1` works like `/1/2`, response is swapped so `a` is the requested first id) |
| DELETE | `/api/runs/<id>` | **204** |
| POST | `/api/explain` | JSON `{"code_a": str, "code_b": str, "language": "python"|"c"}` → `explain()` result; 400 on tokenize errors with the message |
| GET | `/api/evaluation` | contents of `evaluation/results/evaluation.json`; 404 JSON error if absent |

`RunSummary` = `{"id", "name", "created_at" (ISO 8601), "file_count", "pair_count", "high",
"moderate", "low", "max_score", "mean_score", "elapsed_ms"}`.

Zip handling: only extract members with a supported extension, ignore directories, ignore
`__MACOSX/` and hidden files, reject path traversal, enforce the same limits. Duplicate file names
get a numeric suffix. A batch needs at least 2 supported files → otherwise 400.

`run_server.py`: `python run_server.py [--port 5000] [--no-browser]` — starts the app on
`127.0.0.1`, opens the default browser to the app unless `--no-browser`.

`requirements.txt`: pinned versions actually installed in `.venv`.

---------------------------------------------------------------------------------------------

## 8. Frontend — React SPA (frontend agents)

Stack: Vite 8, React 19, `react-router-dom` 7, Tailwind CSS v4 (`@import "tailwindcss";` in
`src/index.css`; plugin already configured in `vite.config.js`), `chart.js` + `react-chartjs-2`,
`axios`. System font stack only. Plain JavaScript (`.jsx`), no TypeScript.

API base URL: relative `/api`. `vite.config.js` must proxy `/api` to `http://127.0.0.1:5000`
for development. Production build (`npm run build`) goes to `frontend/dist` and is served by Flask.

### Routes
| Path | Page component | Owner |
|---|---|---|
| `/` | `pages/Dashboard.jsx` | F1 |
| `/new` | `pages/NewAnalysis.jsx` | F1 |
| `/about` | `pages/About.jsx` | F1 |
| `/runs/:runId` | `pages/RunResults.jsx` | F2 |
| `/runs/:runId/pairs/:aId/:bId` | `pages/PairView.jsx` | F3 |
| `/evaluation` | `pages/Evaluation.jsx` | F4 |
| `/how-it-works` | `pages/HowItWorks.jsx` | F4 |

### Shared foundation (F0 owns; everyone else imports, never edits)
* `src/main.jsx`, `src/App.jsx` (router + layout + all routes), `src/index.css`
* `src/api/client.js` — axios instance `api` with `baseURL: '/api'` and these named exports:
  `getHealth, getDefaults, listRuns, getRun(id), getPair(runId, aId, bId), createRun(formData, onUploadProgress),
   createDemoRun, deleteRun(id), explain({code_a, code_b, language}), getEvaluation`
  each returning `response.data`, plus `errorMessage(err)` that extracts `{error}` or a
  sensible fallback string.
* `src/components/Layout.jsx` — app shell: left sidebar (brand "CodeSentry", nav links:
  Dashboard, New Analysis, Evaluation, How It Works, About) and a content area; responsive.
* `src/components/ui/` — `Card.jsx`, `Button.jsx` (variants primary/secondary/danger/ghost,
  sizes, loading state), `Badge.jsx` (verdict tones High=red, Moderate=amber, Low=green,
  neutral), `Spinner.jsx`, `EmptyState.jsx`, `ErrorBanner.jsx`, `PageHeader.jsx`
  (title, subtitle, actions slot), `StatCard.jsx`, `ScoreBar.jsx` (0–1 value, label, colour by score).
* `src/lib/format.js` — `pct(x)` → `"87.3%"` (`"—"` for null), `score(x)` → 2-decimal string,
  `dateTime(iso)`.
* `src/lib/colors.js` — `scoreColor(x)` continuous colour scale for heat map cells (null → grey),
  `verdictTone(v)`.
* A placeholder component for every page so the app always builds; page owners replace their own page files.

### Visual language
Professional academic tool, light theme (it is screenshotted into a printed report): slate
greys, an indigo primary, red/amber/green only for verdicts, generous whitespace, cards with
subtle borders, consistent 8px spacing rhythm, clear typography hierarchy, visible focus rings,
no emoji. Every page has a `PageHeader`. Every async view has loading, empty and error states.

---------------------------------------------------------------------------------------------

## 9. Dataset — dataset agents

Ten assignment problems. Directory per problem: `dataset/problems/pNN_<slug>/`.

| id | slug | assignment |
|---|---|---|
| p01 | grade_statistics | marks list → mean, median, standard deviation, letter grade distribution, topper |
| p02 | matrix_operations | matrix add, multiply, transpose, 3x3 determinant, print formatted |
| p03 | prime_numbers | primes up to N, count, twin primes, check a number |
| p04 | string_analysis | palindrome check, vowel/consonant count, word frequency, reverse words |
| p05 | bank_account | accounts with deposit, withdraw (insufficient funds), interest, transaction log |
| p06 | sort_and_search | implement a sorting algorithm and binary search, report comparisons |
| p07 | bracket_checker | stack-based balanced bracket checker for several expressions |
| p08 | base_conversion | decimal ↔ binary ↔ octal ↔ hexadecimal conversions implemented manually |
| p09 | inventory_billing | items with quantity and price, discount, 18% GST, itemised bill and total |
| p10 | temperature_series | readings → moving average, min/max with day, longest rising streak |

Per problem, per language (`.py` and `.c`), three files:
* `original.<ext>` — the reference submission
* `independent_1.<ext>`, `independent_2.<ext>` — solutions to the SAME assignment written by
  "different students": genuinely different algorithm choices, decomposition, control flow and
  naming (e.g. sieve vs trial division, bubble vs merge sort, recursion vs iteration). Not
  renamed copies.

Rules for every program:
* 40–110 lines, realistic student style, sensible comments, **at least 3 functions** plus `main`
  (C) / a `main()` called under `if __name__ == "__main__":` (Python).
* **At least one counted `for` loop that contains no `continue` statement** (Python:
  `for i in range(...)`), so the loop-swap obfuscation always has something to convert.
* No user input: hard-coded sample data, deterministic output. Python programs must run to
  completion with exit code 0 using the venv. C programs must parse with tree-sitter-c with no
  `ERROR`/missing nodes and use only `<stdio.h>`, `<stdlib.h>`, `<string.h>`, `<math.h>`,
  `<stdbool.h>`, `<ctype.h>`.
* Plain ASCII source.

`dataset/demo_source/` (demo source agent): the demo class assignment "Assignment 3 — Student
Grade Statistics": `honest_01.py` … `honest_07.py` (seven genuinely different honest Python
solutions) and `honest_c_01.c` (one honest C solution), same rules as above.

### Obfuscator — `dataset/obfuscator.py`
```python
OBFUSCATION_TYPES = ("rename", "comments_format", "reorder", "loop_swap", "dead_code", "combined")
def obfuscate(text: str, language: str, kind: str, seed: int = 0) -> tuple[str, dict]
    # returns (new_text, report) where report = {"kind": ..., "changes": int, "details": [...]}
    # MUST return syntactically valid code (Python: ast.parse; C: tree-sitter with no ERROR/missing)
    # and MUST differ from the input text; raise ValueError otherwise.
```
* `rename` — rename user-defined functions (not `main`), parameters and local/global variables
  to plausible different names; never rename builtins, library functions, imported names,
  attributes, struct fields, dunder names or keywords.
* `comments_format` — remove existing comments, add different comments, change blank-line
  layout; Python: re-indent 4→2 spaces; C: switch brace style (K&R ↔ Allman).
* `reorder` — shuffle the order of top-level function definitions (Python: imports stay first,
  the `if __name__` block stays last; C: insert prototypes for all non-main functions after the
  includes so the file stays valid).
* `loop_swap` — convert counted `for` loops without `continue` into equivalent `while` loops.
* `dead_code` — insert 3–6 unused variables/statements and one never-called helper function.
* `combined` — rename → loop_swap → reorder → dead_code → comments_format.
Python transforms use `ast` + `ast.unparse`; C transforms use tree-sitter to locate nodes and then
apply careful text edits. Deterministic for a given seed.

### Builder — `dataset/build_dataset.py`
`python dataset/build_dataset.py` (idempotent: deletes and recreates its outputs)
* `dataset/generated/<language>/<problem>/original.<ext>`, `independent_1/2.<ext>` (copies),
  `variant_<type>.<ext>` for all six types.
* `dataset/generated/manifest.json` with every obfuscation report.
* `dataset/labels.json`:
  ```json
  {"version": 1, "pairs": [
    {"a": "generated/python/p01_grade_statistics/original.py",
     "b": "generated/python/p01_grade_statistics/variant_rename.py",
     "label": 1, "language": "python", "problem": "p01_grade_statistics",
     "category": "rename"}
  ]}
  ```
  Positives (`label` 1, `category` = obfuscation type): original vs each of its six variants.
  Negatives (`label` 0): original vs `independent_1`, original vs `independent_2`, and
  `independent_1` vs `independent_2` (category `"independent_same_problem"`); `variant_combined`
  vs `independent_1` (category `"obfuscated_vs_independent"`); original of problem p vs original of
  problem q for all p < q within a language (category `"different_problem"`).
  Paths are relative to `dataset/`.
* `dataset/demo_batch/` — `student_01.py` … `student_07.py` = `honest_01..07`;
  `student_08.py` = rename(`honest_02`); `student_09.py` = combined(`honest_05`);
  `student_10.py` = comments_format(`student_09`); `student_11.py` = dead_code(reorder(`honest_07`));
  `student_12.c` = `honest_c_01`; `student_13.c` = loop_swap(`honest_c_01`).
  Plus `dataset/demo_batch/ground_truth.json` and a short `README.md` describing the planted cases.

---------------------------------------------------------------------------------------------

## 10. Evaluation — `evaluation/evaluate.py` (evaluation agent)

`python evaluation/evaluate.py` reads `dataset/labels.json` and scores every pair with five methods:
`text` (plain text baseline), `tfidf` (TF-IDF cosine; IDF computed over all dataset files of that
language), `token` (winnowing Jaccard), `structure` (AST structural similarity), `hybrid`
(fused). For each method:
* confusion matrix, precision, recall, F1, accuracy at the fixed default threshold **0.50**
* the threshold in {0.00, 0.01, …, 1.00} that maximizes F1, and the metrics at that threshold
  (reported separately and clearly labelled as tuned on the same dataset)
* ROC AUC computed with the rank (Mann–Whitney U) formula, ties counted as 0.5
* recall per obfuscation category and false-positive rate per negative category at 0.50
Also timing (mean ms per pair per method) and dataset counts.

Outputs (`evaluation/results/`): `evaluation.json`, `pair_scores.csv`, `summary.md`.
`evaluation.json` shape:
```json
{"generated_at": "ISO 8601", "dataset": {"pairs": 0, "positives": 0, "negatives": 0,
   "by_language": {"python": 0, "c": 0}, "by_category": {"rename": 0}},
 "default_threshold": 0.5,
 "methods": {"hybrid": {"label": "Hybrid (token + structure)",
     "at_default": {"threshold": 0.5, "tp": 0, "fp": 0, "tn": 0, "fn": 0,
                    "precision": 0, "recall": 0, "f1": 0, "accuracy": 0},
     "best": {"threshold": 0.42, "tp": 0, "fp": 0, "tn": 0, "fn": 0,
              "precision": 0, "recall": 0, "f1": 0, "accuracy": 0},
     "auc": 0.0, "mean_ms": 0.0,
     "recall_by_category": {"rename": 0.0},
     "fpr_by_category": {"independent_same_problem": 0.0}}},
 "method_order": ["text", "tfidf", "token", "structure", "hybrid"]}
```
Numbers must come from actually running the code — never typed in by hand.

---------------------------------------------------------------------------------------------

## 11. Tests (tests agent)

`pytest.ini` at the root with `pythonpath = .` and `testpaths = tests`. Test modules:
`test_tokenizers.py`, `test_normalizer.py`, `test_winnowing.py`, `test_tree_similarity.py`,
`test_baselines_fusion.py`, `test_pipeline.py`, `test_obfuscator.py`, `test_api.py`.
The API tests use `create_app({"TESTING": True, "DATABASE_URL": "sqlite:///<tmp>"})` and the Flask
test client. Tests must assert real behaviour (identical files → token 1.0; a renamed copy →
token score 1.0; unrelated programs → low; winnowing tie-break rule; known Zhang–Shasha distances;
upload validation errors; order-insensitive pair route).
