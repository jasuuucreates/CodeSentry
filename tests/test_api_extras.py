"""Model Training endpoint and collusion groups (additions to the API of contract section 7)."""
import pytest

from .conftest import DATASET, PROJECT

pytest.importorskip("flask")
backend_app = pytest.importorskip("backend.app")

REPORT = PROJECT / "training" / "results" / "training_report.json"
FEATURES = PROJECT / "training" / "results" / "features.csv"


def make_client(tmp_path, **overrides):
    database = (tmp_path / "test.db").as_posix()
    config = {"TESTING": True, "DATABASE_URL": f"sqlite:///{database}", **overrides}
    return backend_app.create_app(config).test_client()


def test_training_endpoint_returns_report_and_points(tmp_path):
    if not REPORT.is_file() or not FEATURES.is_file():
        pytest.skip("training/results has not been generated")
    response = make_client(tmp_path).get("/api/training")
    assert response.status_code == 200
    body = response.get_json()
    assert body["report"]["pairs"] == len(body["points"])
    assert {"folds", "comparison_on_held_out_pairs", "logistic_regression"} <= set(body["report"])
    point = body["points"][0]
    assert set(point) == {"token", "structure", "label", "category", "language", "a", "b"}
    assert isinstance(point["token"], float) and isinstance(point["structure"], float)
    assert {p["label"] for p in body["points"]} == {0, 1}


def test_training_endpoint_404_when_report_missing(tmp_path):
    client = make_client(tmp_path, TRAINING_REPORT_FILE=str(tmp_path / "missing.json"))
    response = client.get("/api/training")
    assert response.status_code == 404
    assert "error" in response.get_json()


def test_demo_run_has_the_four_planted_collusion_groups(tmp_path):
    if not (DATASET / "demo_batch").is_dir():
        pytest.skip("dataset/demo_batch has not been built")
    client = make_client(tmp_path)
    run_id = client.post("/api/runs/demo").get_json()["id"]
    run = client.get(f"/api/runs/{run_id}").get_json()
    groups = [sorted(m["name"] for m in cluster["members"]) for cluster in run["clusters"]]
    assert sorted(groups) == sorted([
        ["student_02.py", "student_08.py"],
        ["student_05.py", "student_09.py", "student_10.py"],
        ["student_07.py", "student_11.py"],
        ["student_12.c", "student_13.c"],
    ])
    scores = [cluster["max_score"] for cluster in run["clusters"]]
    assert scores == sorted(scores, reverse=True)
    for cluster in run["clusters"]:
        ids = {m["id"] for m in cluster["members"]}
        assert all(edge["a_id"] in ids and edge["b_id"] in ids for edge in cluster["edges"])
        assert cluster["max_score"] == max(edge["fused"] for edge in cluster["edges"])


def test_unrelated_upload_has_no_collusion_groups(tmp_path):
    client = make_client(tmp_path)
    files = [("a.py", "def f(x):\n    return x * 2\n"),
             ("b.py", "import math\nfor i in range(10):\n    print(math.sqrt(i), i ** 3)\n")]
    import io
    data = {"files": [(io.BytesIO(text.encode()), name) for name, text in files]}
    run_id = client.post("/api/runs", data=data, content_type="multipart/form-data").get_json()["id"]
    assert client.get(f"/api/runs/{run_id}").get_json()["clusters"] == []
