"""Constraint propagation extended with the "fish" family of candidate
eliminations: X-Wing (the 2x2 case) and Swordfish (3x3).

Both work on candidates rather than placements. If a digit can only go in
the same two columns across two different rows, then those two rows must
between them use up that digit in those columns, so no *other* row may
place it there. X-Wing eliminates on that basis; Swordfish is the same
argument stretched across three rows and three columns. Each pattern also
has a transposed form (columns constraining rows), so all four are checked.

Neither ever places a digit by itself. They only narrow candidates, which
then unlocks naked/hidden singles that were previously invisible. That is
exactly why this is worth having next to plain constraint propagation: on
puzzles where the fish patterns bite, the deductions cascade and the
search fallback is needed less often (or not at all).

Because eliminations are invisible on a board of filled digits, the trace
records only real placements, and credits whichever technique unlocked
each one in its `reasoning`. Emitting candidate eliminations as steps
would mean inventing an action the shared schema and visualizer don't
have."""

import time
from itertools import combinations

from app.core import Board, SolveResult, SolveStats, SolveStep, is_complete, is_valid_placement
from app.core.schemas import GRID_SIZE
from app.solvers.base import register

BOX_SIZE = 3

Cell = tuple[int, int]
Candidates = list[list[set[int]]]


def _initial_candidates(cells: list[list[int]]) -> Candidates:
    return [
        [
            (
                {v for v in range(1, 10) if is_valid_placement(cells, r, c, v)}
                if cells[r][c] == 0
                else set()
            )
            for c in range(GRID_SIZE)
        ]
        for r in range(GRID_SIZE)
    ]


def _peers(row: int, col: int) -> set[Cell]:
    box_row, box_col = (row // BOX_SIZE) * BOX_SIZE, (col // BOX_SIZE) * BOX_SIZE
    peers = {(row, c) for c in range(GRID_SIZE)}
    peers |= {(r, col) for r in range(GRID_SIZE)}
    peers |= {
        (r, c)
        for r in range(box_row, box_row + BOX_SIZE)
        for c in range(box_col, box_col + BOX_SIZE)
    }
    peers.discard((row, col))
    return peers


def _units_of(row: int, col: int) -> tuple[list[Cell], ...]:
    """The row, column, and box containing (row, col)."""
    box_row, box_col = (row // BOX_SIZE) * BOX_SIZE, (col // BOX_SIZE) * BOX_SIZE
    return (
        [(row, c) for c in range(GRID_SIZE)],
        [(r, col) for r in range(GRID_SIZE)],
        [
            (r, c)
            for r in range(box_row, box_row + BOX_SIZE)
            for c in range(box_col, box_col + BOX_SIZE)
        ],
    )


def _place(cells: list[list[int]], candidates: Candidates, row: int, col: int, value: int) -> None:
    cells[row][col] = value
    candidates[row][col] = set()
    for r, c in _peers(row, col):
        candidates[r][c].discard(value)


def _find_fish(candidates: Candidates, size: int) -> tuple[str, int] | None:
    """Run one pass of the size-N fish pattern (2 = X-Wing, 3 = Swordfish)
    in both orientations, eliminating candidates in place. Returns the
    technique name and digit if anything was eliminated."""
    for by_rows in (True, False):
        for digit in range(1, 10):
            # For each line, which positions along it could hold this digit.
            positions: dict[int, set[int]] = {}
            for line in range(GRID_SIZE):
                spots = {
                    other
                    for other in range(GRID_SIZE)
                    if digit in (candidates[line][other] if by_rows else candidates[other][line])
                }
                if 2 <= len(spots) <= size:
                    positions[line] = spots

            for chosen in combinations(sorted(positions), size):
                covered: set[int] = set()
                for line in chosen:
                    covered |= positions[line]
                if len(covered) != size:
                    continue

                eliminated = False
                for other in covered:
                    for line in range(GRID_SIZE):
                        if line in chosen:
                            continue
                        cell = candidates[line][other] if by_rows else candidates[other][line]
                        if digit in cell:
                            cell.discard(digit)
                            eliminated = True

                if eliminated:
                    return ("X-Wing" if size == 2 else "Swordfish"), digit
    return None


class FishPatternSolver:
    name = "x_wing_swordfish"

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
        row, col, valid_values = target

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

        self._undo(cells, steps, placed)
        return False

    def _propagate(self, cells: list[list[int]], steps: list[SolveStep]) -> tuple[list[Cell], bool]:
        """Place everything singles can reach; when they stall, try X-Wing
        then Swordfish to narrow candidates and go around again. Returns the
        cells placed, and False if some empty cell ran out of candidates.

        The naked/hidden single passes deliberately mirror
        constraint_propagation's discovery order exactly. Without that, the
        two solvers reach their search fallback holding different boards and
        guess differently, which muddies the comparison: this one would look
        worse than plain propagation on plenty of puzzles for reasons that
        have nothing to do with fish patterns. Matching the order means any
        difference between them is attributable to the eliminations alone."""
        candidates = _initial_candidates(cells)
        placed: list[Cell] = []
        unlocked_by: str | None = None

        def record(row: int, col: int, value: int, technique: str) -> None:
            nonlocal unlocked_by
            _place(cells, candidates, row, col, value)
            reasoning = technique if unlocked_by is None else f"{technique}, after {unlocked_by}"
            steps.append(
                SolveStep(action="place", cell=(row, col), value=value, reasoning=reasoning)
            )
            placed.append((row, col))
            unlocked_by = None

        while True:
            progress = True
            while progress:
                progress = False
                for r in range(GRID_SIZE):
                    for c in range(GRID_SIZE):
                        if cells[r][c] != 0:
                            continue
                        # Bail the moment a cell runs out of candidates rather
                        # than finishing the sweep: in a doomed search branch
                        # every extra placement here is wasted work that still
                        # has to be undone.
                        if not candidates[r][c]:
                            return placed, False
                        if len(candidates[r][c]) == 1:
                            record(r, c, next(iter(candidates[r][c])), "naked single")
                            progress = True

            hidden = self._find_hidden_single(cells, candidates)
            if hidden is not None:
                row, col, value, unit_name = hidden
                record(row, col, value, f"hidden single in {unit_name}")
                continue

            if is_complete(cells):
                return placed, True

            fish = _find_fish(candidates, 2) or _find_fish(candidates, 3)
            if fish is None:
                return placed, True
            technique, digit = fish
            unlocked_by = f"{technique} on {digit}"

    @staticmethod
    def _find_hidden_single(
        cells: list[list[int]], candidates: Candidates
    ) -> tuple[int, int, int, str] | None:
        """A candidate only one cell in a unit can hold. Scans cells in order
        and checks each one's row/column/box, matching how
        constraint_propagation finds these."""
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if cells[r][c] != 0:
                    continue
                for unit_name, unit in zip(("row", "column", "box"), _units_of(r, c)):
                    for value in sorted(candidates[r][c]):
                        if all(
                            value not in candidates[ur][uc]
                            for ur, uc in unit
                            if (ur, uc) != (r, c) and cells[ur][uc] == 0
                        ):
                            return r, c, value, unit_name
        return None

    @staticmethod
    def _undo(cells: list[list[int]], steps: list[SolveStep], placed: list[Cell]) -> None:
        for row, col in reversed(placed):
            value = cells[row][col]
            cells[row][col] = 0
            steps.append(SolveStep(action="remove", cell=(row, col), value=value))

    @staticmethod
    def _most_constrained_empty(cells: list[list[int]]) -> tuple[int, int, set[int]] | None:
        best: tuple[int, int, set[int]] | None = None
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if cells[row][col] != 0:
                    continue
                valid = {v for v in range(1, 10) if is_valid_placement(cells, row, col, v)}
                if best is None or len(valid) < len(best[2]):
                    best = (row, col, valid)
                    if len(valid) <= 1:
                        return best
        return best


register(FishPatternSolver())
