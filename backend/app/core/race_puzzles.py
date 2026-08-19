"""Race-mode puzzle dataset: 100 puzzles each of easy/medium/hard, sourced
from grantm/sudoku-exchange-puzzle-bank (public domain, graded via Sukaku
Explainer) via scripts/import_race_puzzles.py. Committed as a static JSON
fixture — race mode never depends on network access at request time.

Deliberately separate from app/core/puzzles.py, whose small hand-picked set
exists to exercise specific solver behavior (rejects, backtracks, etc.) in
tests — this is a large, difficulty-graded batch for racing algorithms
against each other."""

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from app.core.schemas import Board

Difficulty = Literal["easy", "medium", "hard"]

_DATA_PATH = Path(__file__).parent / "data" / "race_puzzles.json"


class RacePuzzle(BaseModel):
    id: str
    board: Board
    solution: Board
    rating: float


def _load() -> dict[str, list[RacePuzzle]]:
    raw = json.loads(_DATA_PATH.read_text())
    return {
        difficulty: [
            RacePuzzle(
                id=p["id"],
                board=Board(cells=p["cells"]),
                solution=Board(cells=p["solution"]),
                rating=p["rating"],
            )
            for p in puzzles
        ]
        for difficulty, puzzles in raw.items()
    }


_PUZZLES_BY_DIFFICULTY = _load()


def get_race_puzzles(difficulty: Difficulty) -> list[RacePuzzle]:
    return _PUZZLES_BY_DIFFICULTY[difficulty]
