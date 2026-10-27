"""Flask REST API (contract section 7), exercised through the Flask test client."""
import io
import json
import zipfile

import pytest

from .conftest import DATASET, PROJECT

pytest.importorskip("flask")
if not (PROJECT / "backend" / "app.py").exists():
    pytest.skip("backend/app.py does not exist yet", allow_module_level=True)
backend_app = pytest.importorskip("backend.app")

SUMMARY_KEYS = {"id", "name", "created_at", "file_count", "pair_count", "high", "moderate", "low", "max_score",
                "mean_score", "elapsed_ms"}


@pytest.fixture
def client(tmp_path):
    database = (tmp_path / "test.db").as_posix()
    app = backend_app.create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{database}"})
    with app.test_client() as test_client:
        yield test_client


def upload(client, files, **form):
    data = {key: value for key, value in form.items()}
    data["files"] = [(io.BytesIO(content.encode("utf-8") if isinstance(content, str) else content), name)
                     for name, content in files]
    return client.post("/api/runs", data=data, content_type="multipart/form-data")


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "version": "1.0.0", "languages": ["python", "c"]}


def test_config_defaults(client):
    body = client.get("/api/config/defaults").get_json()
    for key in ("k", "w", "w_token", "w_structure", "high_threshold", "moderate_threshold", "ted_node_cap"):
        assert key in body


def test_upload_requires_files(client):
    response = client.post("/api/runs", data={}, content_type="multipart/form-data")
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_upload_rejects_single_file(client, py_program):
    response = upload(client, [("only.py", py_program)])
    assert response.status_code == 400
    assert "at least 2" in response.get_json()["error"]


def test_upload_rejects_unsupported_extension(client, py_program):
    response = upload(client, [("a.py", py_program), ("notes.txt", "hello")])
    assert response.status_code == 400
    assert ".txt" in response.get_json()["error"]


def test_upload_rejects_invalid_setting(client, py_program, py_renamed):
    response = upload(client, [("a.py", py_program), ("b.py", py_renamed)], k="0")
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_run_lifecycle_and_order_insensitive_pair_route(client, py_program, py_renamed, py_unrelated):
    response = upload(client, [("a.py", py_program), ("b.py", py_renamed), ("c.py", py_unrelated)], name="Lab 1")
    assert response.status_code == 201
    summary = response.get_json()
    assert set(summary) >= SUMMARY_KEYS
    assert summary["file_count"] == 3 and summary["pair_count"] == 3 and summary["name"] == "Lab 1"

    run = client.get(f"/api/runs/{summary['id']}").get_json()
    assert {"files", "matrix", "pairs", "config"} <= set(run)
    assert all("a_source" not in pair for pair in run["pairs"])
    ids = {f["name"]: f["id"] for f in run["files"]}
    a, b = ids["a.py"], ids["b.py"]

    forward = client.get(f"/api/runs/{summary['id']}/pairs/{a}/{b}")
    backward = client.get(f"/api/runs/{summary['id']}/pairs/{b}/{a}")
    assert forward.status_code == 200 and backward.status_code == 200
    fwd, bwd = forward.get_json(), backward.get_json()
    assert fwd["a_id"] == a and fwd["b_id"] == b
    assert bwd["a_id"] == b and bwd["b_id"] == a
    assert fwd["scores"] == bwd["scores"]
    assert fwd["scores"]["token"] == 1.0
    assert fwd["a_source"] == py_program and bwd["a_source"] == py_renamed
    for m_f, m_b in zip(sorted(fwd["matches"], key=lambda m: (m["a_start"], m["b_start"])),
                        sorted(bwd["matches"], key=lambda m: (m["b_start"], m["a_start"]))):
        assert (m_f["a_start"], m_f["b_start"]) == (m_b["b_start"], m_b["a_start"])

    runs = client.get("/api/runs").get_json()
    assert [r["id"] for r in runs] == [summary["id"]]
    assert client.delete(f"/api/runs/{summary['id']}").status_code == 204
    missing = client.get(f"/api/runs/{summary['id']}")
    assert missing.status_code == 404 and "error" in missing.get_json()


def test_unknown_pair_and_run_are_404(client, py_program, py_renamed):
    summary = upload(client, [("a.py", py_program), ("b.py", py_renamed)]).get_json()
    assert client.get(f"/api/runs/{summary['id']}/pairs/9999/1").status_code == 404
    assert client.get("/api/runs/424242").status_code == 404


def test_zip_upload_ignores_junk(client, py_program, py_renamed, c_program):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("lab/a.py", py_program)
        archive.writestr("lab/b.py", py_renamed)
        archive.writestr("lab/c.c", c_program)
        archive.writestr("__MACOSX/lab/._a.py", "junk")
        archive.writestr("lab/.hidden.py", "x = 1\n")
        archive.writestr("lab/readme.txt", "not code")
    response = upload(client, [("class.zip", buffer.getvalue())])
    assert response.status_code == 201
    body = response.get_json()
    assert body["file_count"] == 3
    assert body["pair_count"] == 1                # only the two Python files are compared


def test_explain_endpoint(client, py_program, py_renamed):
    response = client.post("/api/explain", json={"code_a": py_program, "code_b": py_renamed, "language": "python"})
    assert response.status_code == 200
    body = response.get_json()
    assert set(body) == {"language", "a", "b", "result"}
    assert body["result"]["scores"]["token"] == 1.0
    bad = client.post("/api/explain", json={"code_a": "s = 'oops\n", "code_b": "x = 1\n", "language": "python"})
    assert bad.status_code == 400 and "error" in bad.get_json()


def test_demo_run(client):
    if not (DATASET / "demo_batch").is_dir():
        pytest.skip("dataset/demo_batch has not been built")
    response = client.post("/api/runs/demo")
    assert response.status_code == 201
    body = response.get_json()
    assert body["file_count"] == 13
    assert body["pair_count"] == 55 + 1          # 11 Python files -> 55 pairs, 2 C files -> 1 pair


def test_evaluation_endpoint(client):
    response = client.get("/api/evaluation")
    results = PROJECT / "evaluation" / "results" / "evaluation.json"
    if not results.exists():
        assert response.status_code == 404
        return
    assert response.status_code == 200
    body = response.get_json()
    assert body["method_order"][:5] == ["text", "tfidf", "token", "structure", "hybrid"]
    assert body == json.loads(results.read_text(encoding="utf-8"))


def test_unknown_api_route_is_json_404(client):
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert "error" in response.get_json()
