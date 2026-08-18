"""Constraint propagation (naked singles + hidden singles), falling back to
MRV-ordered backtracking search only for whatever a puzzle's logic can't
resolve on its own. Unlike plain backtracking, most cells get filled by
deduction rather than trial and error — a genuinely different algorithm,
not just a tuned version of the first one.

Where it does fall back to search, the trace shows every digit 1-9 tried
at a cell (including instant rejects), same as the backtracking solver —
so the two are visibly comparable on the cells where this one also has to
guess."""

import time

from app.core import Board, SolveResult, SolveStats, SolveStep, is_complete, is_valid_placement
from app.core.schemas import GRID_SIZE
from app.solvers.base import register

BOX_SIZE = 3

Cell = tuple[int, int]


def _candidates(cells: list[list[int]], row: int, col: int) -> list[int]:
    return [v for v in range(1, 10) if is_valid_placement(cells, row, col, v)]


def _empty_cells(cells: list[list[int]]) -> list[Cell]:
    return [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if cells[r][c] == 0]


def _units(row: int, col: int) -> tuple[list[Cell], ...]:
    """The row, column, and box peer-cell coordinates containing (row, col)."""
    box_row, box_col = (row // BOX_SIZE) * BOX_SIZE, (col // BOX_SIZE) * BOX_SIZE
    row_unit = [(row, c) for c in range(GRID_SIZE)]
    col_unit = [(r, col) for r in range(GRID_SIZE)]
    box_unit = [
        (r, c)
        for r in range(box_row, box_row + BOX_SIZE)
        for c in range(box_col, box_col + BOX_SIZE)
    ]
    return row_unit, col_unit, box_unit


class ConstraintPropagationSolver:
    name = "constraint_propagation"

    def solve(self, board: Board) -> SolveResult:
        cells = [row[:] for row in board.cells]
        given_count = sum(1 for row in cells for value in row if value != 0)
        steps: list[SolveStep] = []

        start = time.perf_counter()
        solved = self._solve(cells, steps)
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

    def _solve(self, cells: list[list[int]], steps: list[SolveStep]) -> bool:
        placed, ok = self._propagate(cells, steps)
        if not ok:
            self._undo(cells, steps, placed)
            return False

        if is_complete(cells):
            return True

        target = self._most_constrained_empty(cells)
        if target is None:
            self._undo(cells, steps, placed)
            return False
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

            if is_valid and self._solve(cells, steps):
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

        # This frame's own propagation may have placed cells before the guess
        # loop ran (or before a contradiction was found) — undo those too, or
        # the caller's board is left inconsistent with what it started with.
        self._undo(cells, steps, placed)
        return False

    def _propagate(self, cells: list[list[int]], steps: list[SolveStep]) -> tuple[list[Cell], bool]:
        """Repeatedly place any cell forced by a naked or hidden single.
        Returns the cells it placed, and False if a cell was left with zero
        legal candidates — proof this branch is unsolvable."""
        placed: list[Cell] = []
        progress = True
        while progress:
            progress = False

            for row, col in _empty_cells(cells):
                candidates = _candidates(cells, row, col)
                if len(candidates) == 0:
                    return placed, False
                if len(candidates) == 1:
                    cells[row][col] = candidates[0]
                    steps.append(
                        SolveStep(
                            action="place",
                            cell=(row, col),
                            value=candidates[0],
                            reasoning="naked single",
                        )
                    )
                    placed.append((row, col))
                    progress = True

            if progress:
                continue

            for row, col in _empty_cells(cells):
                candidates = _candidates(cells, row, col)
                found = self._find_hidden_single(cells, row, col, candidates)
                if found is not None:
                    value, unit_name = found
                    cells[row][col] = value
                    steps.append(
                        SolveStep(
                            action="place",
                            cell=(row, col),
                            value=value,
                            reasoning=f"hidden single in {unit_name}",
                        )
                    )
                    placed.append((row, col))
                    progress = True
                    break

        return placed, True

    @staticmethod
    def _undo(cells: list[list[int]], steps: list[SolveStep], placed: list[Cell]) -> None:
        for row, col in reversed(placed):
            value = cells[row][col]
            cells[row][col] = 0
            steps.append(SolveStep(action="remove", cell=(row, col), value=value))

    @staticmethod
    def _find_hidden_single(
        cells: list[list[int]], row: int, col: int, candidates: list[int]
    ) -> tuple[int, str] | None:
        """A candidate that only (row, col) can hold within one of its units."""
        for unit_name, unit in zip(("row", "column", "box"), _units(row, col)):
            for value in candidates:
                if all(
                    value not in _candidates(cells, r, c)
                    for r, c in unit
                    if (r, c) != (row, col) and cells[r][c] == 0
                ):
                    return value, unit_name
        return None

    @staticmethod
    def _most_constrained_empty(cells: list[list[int]]) -> tuple[int, int, list[int]] | None:
        best: tuple[int, int, list[int]] | None = None
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if cells[row][col] != 0:
                    continue
                candidates = _candidates(cells, row, col)
                if best is None or len(candidates) < len(best[2]):
                    best = (row, col, candidates)
                    if len(candidates) <= 1:
                        return best
        return best


register(ConstraintPropagationSolver())
