import time

from fastapi.testclient import TestClient

from app.core.puzzles import MEDIUM_CELLS
from app.core.race_puzzles import RacePuzzle
from app.core.schemas import Board
from app.main import app
from app.solvers import list_solvers
from tests.test_backtracking import EASY

client = TestClient(app)

# Deliberately fast puzzles — these tests are about the start/poll
# plumbing, not timing robustness.
FAKE_PUZZLES = [
    RacePuzzle(id="fake-1", board=Board(cells=EASY), solution=Board(cells=EASY), rating=1.0),
    RacePuzzle(
        id="fake-2", board=Board(cells=MEDIUM_CELLS), solution=Board(cells=MEDIUM_CELLS), rating=2.0
    ),
]


def _fake_get_race_puzzles(difficulty: str) -> list[RacePuzzle]:
    return FAKE_PUZZLES


def _poll_until_all_done(race_id: str, timeout: float = 20.0) -> dict:
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        response = client.get(f"/race/{race_id}/progress")
        assert response.status_code == 200
        body = response.json()
        if all(algo["done"] for algo in body["algorithms"].values()):
            return body
        time.sleep(0.1)
    raise TimeoutError("race did not finish within test timeout")


def test_start_returns_a_race_id_and_the_full_algorithm_list(monkeypatch) -> None:
    monkeypatch.setattr("app.api.race.get_race_puzzles", _fake_get_race_puzzles)

    response = client.post("/race/start", params={"difficulty": "easy"})
    assert response.status_code == 200

    body = response.json()
    assert body["race_id"]
    assert set(body["algorithms"]) == set(list_solvers())
    assert body["puzzle_count"] == 2


def test_invalid_difficulty_returns_422() -> None:
    response = client.post("/race/start", params={"difficulty": "impossible"})
    assert response.status_code == 422


def test_unknown_race_id_returns_404() -> None:
    response = client.get("/race/does-not-exist/progress")
    assert response.status_code == 404


def test_polling_reaches_completion_with_dense_ordered_results(monkeypatch) -> None:
    monkeypatch.setattr("app.api.race.get_race_puzzles", _fake_get_race_puzzles)

    start_response = client.post("/race/start", params={"difficulty": "easy"})
    race_id = start_response.json()["race_id"]

    final = _poll_until_all_done(race_id)

    for algorithm, progress in final["algorithms"].items():
        assert progress["done"] is True
        assert len(progress["results"]) == 2
        assert progress["results"][0]["puzzle_id"] == "fake-1"
        assert progress["results"][1]["puzzle_id"] == "fake-2"
        assert "steps" not in progress["results"][0]  # no step trace in race mode


def test_real_dataset_races_end_to_end() -> None:
    """One real (unmocked) race against the actual committed dataset, so
    this stays quick while still exercising the real fixture and every
    registered algorithm end-to-end."""
    start_response = client.post("/race/start", params={"difficulty": "easy"})
    race_id = start_response.json()["race_id"]

    final = _poll_until_all_done(race_id, timeout=35.0)

    # Exact solvers are complete on easy puzzles; the deliberately
    # imperfect ones (simulated_annealing, neural_net) aren't asserted here.
    for algorithm in ("backtracking", "constraint_propagation", "dancing_links"):
        progress = final["algorithms"][algorithm]
        assert len(progress["results"]) == 100
        assert all(r["solved"] for r in progress["results"])
