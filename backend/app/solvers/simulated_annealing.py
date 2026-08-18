"""Simulated annealing — unlike the other solvers, this is a stochastic
local-search heuristic, not a complete algorithm: it isn't guaranteed to
find a solution and gives up after a fixed iteration budget. Included
deliberately to prove the visualizer tolerates a fundamentally different
kind of trace: cells getting reassigned and swapped, not just filled in
and backtracked.

Each 3x3 box is filled once with a random permutation of its missing
digits (so box constraints hold by construction and are never broken),
then pairs of non-given cells within the same box are repeatedly swapped,
accepting swaps that reduce row/column conflicts and occasionally
accepting ones that don't (via the Metropolis criterion) to escape local
minima. A swap is traced as remove-then-place on each of the two cells."""

import math
import random
import time

from app.core import Board, SolveResult, SolveStats, SolveStep
from app.core.schemas import GRID_SIZE
from app.solvers.base import register

BOX_SIZE = 3
MAX_ITERATIONS = 60_000
INITIAL_TEMPERATURE = 0.6
COOLING_RATE = 0.999
REHEAT_AFTER_STALE_ITERATIONS = 2_000
SEED = 0

Cell = tuple[int, int]


def _box_cells(box_row: int, box_col: int) -> list[Cell]:
    r0, c0 = box_row * BOX_SIZE, box_col * BOX_SIZE
    return [(r, c) for r in range(r0, r0 + BOX_SIZE) for c in range(c0, c0 + BOX_SIZE)]


def _line_conflicts(values: list[int]) -> int:
    counts: dict[int, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return sum(count - 1 for count in counts.values() if count > 1)


def _row_col_conflicts(cells: list[list[int]]) -> int:
    conflicts = 0
    for i in range(GRID_SIZE):
        conflicts += _line_conflicts(cells[i])
        conflicts += _line_conflicts([cells[r][i] for r in range(GRID_SIZE)])
    return conflicts


class SimulatedAnnealingSolver:
    name = "simulated_annealing"

    def solve(self, board: Board) -> SolveResult:
        cells = [row[:] for row in board.cells]
        given_mask = [[value != 0 for value in row] for row in cells]
        given_count = sum(1 for row in given_mask for is_given in row if is_given)

        rng = random.Random(SEED)
        steps: list[SolveStep] = []

        start = time.perf_counter()
        solved = self._run(cells, given_mask, rng, steps)
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

    def _run(
        self,
        cells: list[list[int]],
        given_mask: list[list[bool]],
        rng: random.Random,
        steps: list[SolveStep],
    ) -> bool:
        self._random_restart(cells, given_mask, rng, steps)
        cost = _row_col_conflicts(cells)

        boxes = [(br, bc) for br in range(BOX_SIZE) for bc in range(BOX_SIZE)]
        swappable_by_box = {
            box: [cell for cell in _box_cells(*box) if not given_mask[cell[0]][cell[1]]]
            for box in boxes
        }
        swappable_boxes = [box for box in boxes if len(swappable_by_box[box]) >= 2]
        if not swappable_boxes:
            return cost == 0

        temperature = INITIAL_TEMPERATURE
        stale = 0

        for _ in range(MAX_ITERATIONS):
            if cost == 0:
                return True

            box = rng.choice(swappable_boxes)
            (r1, c1), (r2, c2) = rng.sample(swappable_by_box[box], 2)

            delta = self._swap_delta(cells, r1, c1, r2, c2)
            if delta <= 0 or rng.random() < math.exp(-delta / max(temperature, 1e-6)):
                old1, old2 = cells[r1][c1], cells[r2][c2]
                steps.append(SolveStep(action="remove", cell=(r1, c1), value=old1))
                steps.append(SolveStep(action="remove", cell=(r2, c2), value=old2))
                cells[r1][c1], cells[r2][c2] = old2, old1
                steps.append(
                    SolveStep(action="place", cell=(r1, c1), value=old2, reasoning="anneal")
                )
                steps.append(
                    SolveStep(action="place", cell=(r2, c2), value=old1, reasoning="anneal")
                )
                cost += delta
                stale = 0 if delta != 0 else stale + 1
            else:
                stale += 1

            temperature *= COOLING_RATE
            if stale >= REHEAT_AFTER_STALE_ITERATIONS:
                self._random_restart(cells, given_mask, rng, steps)
                cost = _row_col_conflicts(cells)
                temperature = INITIAL_TEMPERATURE
                stale = 0

        return cost == 0

    @staticmethod
    def _swap_delta(cells: list[list[int]], r1: int, c1: int, r2: int, c2: int) -> int:
        """Change in row/column conflict count a swap of these two cells
        would cause, without permanently performing the swap."""
        rows, cols = {r1, r2}, {c1, c2}
        before = sum(_line_conflicts(cells[r]) for r in rows)
        before += sum(_line_conflicts([cells[r][c] for r in range(GRID_SIZE)]) for c in cols)

        cells[r1][c1], cells[r2][c2] = cells[r2][c2], cells[r1][c1]
        after = sum(_line_conflicts(cells[r]) for r in rows)
        after += sum(_line_conflicts([cells[r][c] for r in range(GRID_SIZE)]) for c in cols)
        cells[r1][c1], cells[r2][c2] = cells[r2][c2], cells[r1][c1]

        return after - before

    @staticmethod
    def _random_restart(
        cells: list[list[int]],
        given_mask: list[list[bool]],
        rng: random.Random,
        steps: list[SolveStep],
    ) -> None:
        """Refill every non-given cell with a random permutation of each
        box's missing digits — box constraints hold by construction."""
        for box_row in range(BOX_SIZE):
            for box_col in range(BOX_SIZE):
                box = _box_cells(box_row, box_col)
                used = {cells[r][c] for r, c in box if given_mask[r][c]}
                missing = [v for v in range(1, 10) if v not in used]
                rng.shuffle(missing)
                values = iter(missing)

                for r, c in box:
                    if given_mask[r][c]:
                        continue
                    new_value = next(values)
                    old_value = cells[r][c]
                    if old_value != 0:
                        steps.append(SolveStep(action="remove", cell=(r, c), value=old_value))
                    cells[r][c] = new_value
                    steps.append(
                        SolveStep(
                            action="place", cell=(r, c), value=new_value, reasoning="random init"
                        )
                    )


register(SimulatedAnnealingSolver())
