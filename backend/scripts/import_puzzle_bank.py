"""One-time import: pulls graded puzzles from grantm/sudoku-exchange-puzzle-
bank (public domain, https://github.com/grantm/sudoku-exchange-puzzle-bank)
and writes a trimmed, solved, self-contained fixture to
app/core/data/puzzle_bank.json. The app reads only that committed file —
no network access at request time, same "eager-compute, no live external
calls" philosophy as the rest of this app.

The source files have no solutions, so this script solves each candidate
puzzle itself (via BacktrackingSolver) and stores the solution alongside it,
both so nothing downstream needs to re-derive it, and so tests can cross-
check every algorithm's output against a known-correct answer.

Plain backtracking has no completeness guarantee on *time* — a handful of
puzzles in the harder buckets take minutes, not milliseconds, for MRV
backtracking to crack (one in the "hard" bucket ran over 3 minutes before
being killed during dataset curation). Every candidate is therefore solved
with a hard wall-clock cap here at import time; anything that blows the cap
is skipped in favor of the next candidate, so no puzzle that ships can
stall the app later.

Usage (from backend/, with the venv active):
    python -m scripts.import_puzzle_bank
"""

import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.schemas import Board  # noqa: E402
from app.core.timeout import solve_with_timeout  # noqa: E402
from app.solvers.backtracking import BacktrackingSolver  # noqa: E402

SOURCE_BASE = "https://raw.githubusercontent.com/grantm/sudoku-exchange-puzzle-bank/master"
DIFFICULTIES = ("easy", "medium", "hard")
PUZZLES_PER_DIFFICULTY = 100
CANDIDATE_LINES = 2000  # read this many lines per bucket, in case some get skipped
SOLVE_TIME_CAP_SECONDS = 0.5
OUT_PATH = Path(__file__).resolve().parent.parent / "app" / "core" / "data" / "puzzle_bank.json"


def parse_line(line: str) -> tuple[str, list[list[int]], float]:
    puzzle_hash, digits, rating = line.split()
    cells = [[int(digits[row * 9 + col]) for col in range(9)] for row in range(9)]
    return puzzle_hash, cells, float(rating)


def fetch_puzzles(difficulty: str, count: int) -> list[dict]:
    url = f"{SOURCE_BASE}/{difficulty}.txt"
    print(f"fetching {url}")
    with urllib.request.urlopen(url) as response:
        lines = response.read().decode("utf-8").splitlines()[:CANDIDATE_LINES]

    solver = BacktrackingSolver()
    puzzles = []
    skipped_slow = 0
    for line in lines:
        if len(puzzles) >= count:
            break
        puzzle_hash, cells, rating = parse_line(line)
        result = solve_with_timeout(solver, Board(cells=cells), SOLVE_TIME_CAP_SECONDS)
        if result is None:
            skipped_slow += 1
            continue
        if not result.solved:
            # Shouldn't happen for a validly-generated, unique-solution
            # puzzle — skip defensively rather than ship a broken fixture.
            print(f"  WARNING: {puzzle_hash} did not solve, skipping")
            continue
        puzzles.append(
            {
                "id": f"{difficulty}-{puzzle_hash}",
                "cells": cells,
                "solution": result.solved_board.cells,
                "rating": rating,
            }
        )
    print(f"  kept {len(puzzles)}/{count} (skipped {skipped_slow} slow ones)")
    return puzzles


def main() -> None:
    dataset = {
        difficulty: fetch_puzzles(difficulty, PUZZLES_PER_DIFFICULTY) for difficulty in DIFFICULTIES
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(dataset))
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
