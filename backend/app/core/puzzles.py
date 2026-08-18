"""A fixed, curated set of puzzles for benchmarking and race mode — a single
source of truth so "easy" and "hard" mean the same thing in tests, the
benchmark history, and the frontend's puzzle picker."""

from typing import Literal

from pydantic import BaseModel

from app.core.schemas import Board

Difficulty = Literal["easy", "medium", "hard"]


class BenchmarkPuzzle(BaseModel):
    id: str
    name: str
    difficulty: Difficulty
    board: Board
    given_count: int


def _puzzle(id: str, name: str, difficulty: Difficulty, cells: list[list[int]]) -> BenchmarkPuzzle:
    given_count = sum(1 for row in cells for value in row if value != 0)
    return BenchmarkPuzzle(
        id=id, name=name, difficulty=difficulty, board=Board(cells=cells), given_count=given_count
    )


EASY_CELLS = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]

MEDIUM_CELLS = [
    [0, 2, 0, 6, 0, 8, 0, 0, 0],
    [5, 8, 0, 0, 0, 9, 7, 0, 0],
    [0, 0, 0, 0, 4, 0, 0, 0, 0],
    [3, 7, 0, 0, 0, 0, 5, 0, 0],
    [6, 0, 0, 0, 0, 0, 0, 0, 4],
    [0, 0, 8, 0, 0, 0, 0, 1, 3],
    [0, 0, 0, 0, 2, 0, 0, 0, 0],
    [0, 0, 9, 8, 0, 0, 0, 3, 6],
    [0, 0, 0, 3, 0, 6, 0, 9, 0],
]

# A well-known "hard" puzzle (not a pathological worst case, but sparse
# enough to exercise real backtracking — empirically ~80x slower to solve
# than EASY above).
HARD_CELLS = [
    [0, 0, 0, 0, 0, 0, 0, 1, 2],
    [0, 0, 0, 0, 0, 0, 0, 0, 3],
    [0, 0, 2, 3, 0, 0, 4, 0, 0],
    [0, 0, 1, 8, 0, 0, 0, 0, 5],
    [0, 6, 0, 0, 7, 0, 8, 0, 0],
    [0, 0, 0, 0, 0, 9, 0, 0, 0],
    [0, 0, 8, 5, 0, 0, 0, 0, 0],
    [9, 0, 0, 0, 4, 0, 5, 0, 0],
    [4, 7, 0, 0, 0, 6, 0, 0, 0],
]

BENCHMARK_PUZZLES: list[BenchmarkPuzzle] = [
    _puzzle("easy-1", "Easy", "easy", EASY_CELLS),
    _puzzle("medium-1", "Medium", "medium", MEDIUM_CELLS),
    _puzzle("hard-1", "Hard", "hard", HARD_CELLS),
]

_PUZZLES_BY_ID = {puzzle.id: puzzle for puzzle in BENCHMARK_PUZZLES}


def get_puzzle(puzzle_id: str) -> BenchmarkPuzzle | None:
    return _PUZZLES_BY_ID.get(puzzle_id)
