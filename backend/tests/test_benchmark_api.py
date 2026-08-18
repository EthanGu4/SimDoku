import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_benchmark_db(tmp_path, monkeypatch):
    """Every test here hits the real API surface, including persistence —
    point it at a throwaway DB so tests never touch backend/benchmark.db."""
    monkeypatch.setattr("app.core.history.DEFAULT_DB_PATH", tmp_path / "test.db")


def test_lists_benchmark_puzzles() -> None:
    response = client.get("/puzzles")
    assert response.status_code == 200

    puzzles = response.json()
    ids = [p["id"] for p in puzzles]
    assert "easy-1" in ids
    assert all(p["given_count"] > 0 for p in puzzles)


def test_runs_and_persists_a_benchmark() -> None:
    response = client.post("/benchmark/backtracking", json={"puzzle_id": "easy-1"})
    assert response.status_code == 200

    body = response.json()
    assert body["solved"] is True
    assert body["stats"]["algorithm"] == "backtracking"

    history = client.get("/benchmark/history", params={"puzzle_id": "easy-1"})
    assert history.status_code == 200
    runs = history.json()
    assert len(runs) == 1
    assert runs[0]["algorithm"] == "backtracking"
    assert runs[0]["puzzle_id"] == "easy-1"


def test_history_filters_by_puzzle() -> None:
    client.post("/benchmark/backtracking", json={"puzzle_id": "easy-1"})
    client.post("/benchmark/dancing_links", json={"puzzle_id": "hard-1"})

    easy_runs = client.get("/benchmark/history", params={"puzzle_id": "easy-1"}).json()
    assert {run["puzzle_id"] for run in easy_runs} == {"easy-1"}


def test_unknown_algorithm_returns_404() -> None:
    response = client.post("/benchmark/does-not-exist", json={"puzzle_id": "easy-1"})
    assert response.status_code == 404


def test_unknown_puzzle_returns_404() -> None:
    response = client.post("/benchmark/backtracking", json={"puzzle_id": "does-not-exist"})
    assert response.status_code == 404
