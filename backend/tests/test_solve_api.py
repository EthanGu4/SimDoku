from fastapi.testclient import TestClient

from app.main import app
from tests.test_backtracking import EASY

client = TestClient(app)


def test_lists_registered_algorithms() -> None:
    response = client.get("/solve/algorithms")
    assert response.status_code == 200
    assert "backtracking" in response.json()


def test_solve_endpoint_solves_puzzle() -> None:
    response = client.post("/solve/backtracking", json={"cells": EASY})
    assert response.status_code == 200

    body = response.json()
    assert body["solved"] is True
    assert body["stats"]["algorithm"] == "backtracking"


def test_unknown_algorithm_returns_404() -> None:
    response = client.post("/solve/does-not-exist", json={"cells": EASY})
    assert response.status_code == 404


def test_board_with_rule_violation_returns_400() -> None:
    invalid = [row[:] for row in EASY]
    invalid[0][1] = invalid[0][0]  # duplicate within the same row

    response = client.post("/solve/backtracking", json={"cells": invalid})
    assert response.status_code == 400


def test_malformed_board_returns_422() -> None:
    response = client.post("/solve/backtracking", json={"cells": [[1, 2, 3]]})
    assert response.status_code == 422
