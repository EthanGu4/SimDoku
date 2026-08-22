"""The graded puzzle bank: 100 puzzles each of easy/medium/hard, sourced
from grantm/sudoku-exchange-puzzle-bank (public domain, graded via Sukaku
Explainer) via scripts/import_puzzle_bank.py. Committed as a static JSON
fixture, so nothing here depends on network access at request time.

Deliberately separate from app/core/puzzles.py, whose small hand-picked set
exists to exercise specific solver behavior (rejects, backtracks, etc.) in
tests. This is a large, difficulty-graded bank used to hand the comparison
view a real puzzle to run every algorithm against."""

import json
import random
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from app.core.schemas import Board

Difficulty = Literal["easy", "medium", "hard"]

_DATA_PATH = Path(__file__).parent / "data" / "puzzle_bank.json"


class BankPuzzle(BaseModel):
    id: str
    board: Board
    solution: Board
    rating: float


def _load() -> dict[str, list[BankPuzzle]]:
    raw = json.loads(_DATA_PATH.read_text())
    return {
        difficulty: [
            BankPuzzle(
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


def get_puzzles(difficulty: Difficulty) -> list[BankPuzzle]:
    return _PUZZLES_BY_DIFFICULTY[difficulty]


def get_random_puzzle(difficulty: Difficulty) -> BankPuzzle:
    return random.choice(_PUZZLES_BY_DIFFICULTY[difficulty])
