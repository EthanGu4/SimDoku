"""Plain recursive backtracking with minimum-remaining-values cell ordering:
at each step, branch on the empty cell with the fewest legal candidates.
This is still brute-force search (no constraint propagation/elimination
across cells) — just a cheap ordering choice that keeps worst-case puzzles
tractable.

The trace shows every digit 1-9 tried at each cell, not just the ones that
survive a pre-filter — including ones instantly rejected for conflicting
with a peer — so the visualizer can show the algorithm's actual trial-and-
error, not just its successful placements."""

import time

from app.core import Board, SolveResult, SolveStats, SolveStep, is_valid_placement
from app.core.schemas import GRID_SIZE
from app.solvers.base import register


class BacktrackingSolver:
    name = "backtracking"

    def solve(self, board: Board) -> SolveResult:
        cells = [row[:] for row in board.cells]
        given_count = sum(1 for row in cells for value in row if value != 0)
        steps: list[SolveStep] = []

        start = time.perf_counter()
        solved = self._backtrack(cells, steps)
        elapsed = time.perf_counter() - start

        return SolveResult(
            solved=solved,
            solved_board=Board(cells=cells),
            steps=steps,
            stats=SolveStats(
                algorithm=self.name,
                elapsed_time=elapsed,
                step_count=len(steps),
                given_count=given_count,
            ),
        )

    def _backtrack(self, cells: list[list[int]], steps: list[SolveStep]) -> bool:
        target = self._most_constrained_empty(cells)
        if target is None:
            return True
        row, col, candidates = target
        valid_values = set(candidates)

        for value in range(1, 10):
            is_valid = value in valid_values
            cells[row][col] = value
            steps.append(
                SolveStep(
                    action="place",
                    cell=(row, col),
                    value=value,
                    reasoning="search" if is_valid else "reject",
                )
            )

            if is_valid and self._backtrack(cells, steps):
                return True

            cells[row][col] = 0
            steps.append(
                SolveStep(
                    action="remove",
                    cell=(row, col),
                    value=value,
                    reasoning="backtrack" if is_valid else None,
                )
            )

        return False

    @staticmethod
    def _most_constrained_empty(
        cells: list[list[int]],
    ) -> tuple[int, int, list[int]] | None:
        """The empty cell with the fewest legal candidates (minimum
        remaining values), so dead ends are hit — and pruned — as early as
        possible."""
        best: tuple[int, int, list[int]] | None = None
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if cells[row][col] != 0:
                    continue
                candidates = [v for v in range(1, 10) if is_valid_placement(cells, row, col, v)]
                if best is None or len(candidates) < len(best[2]):
                    best = (row, col, candidates)
                    if len(candidates) <= 1:
                        return best
        return best


register(BacktrackingSolver())
