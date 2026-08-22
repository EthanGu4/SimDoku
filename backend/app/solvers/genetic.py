"""A genetic algorithm: Sudoku by artificial evolution.

Each organism is a whole candidate grid. Every 3x3 box is seeded with a
random permutation of the digits it's missing, so box constraints hold by
construction and no operator is ever allowed to break them. Fitness is the
number of row and column conflicts, which makes 0 the solution. Each
generation keeps a few elites, then breeds the rest: tournament selection
picks two parents, crossover builds a child by inheriting each box whole
from one parent or the other, and mutation swaps two non-given cells inside
a random box.

Inheriting whole boxes is what makes this feel different from simulated
annealing, which is the other stochastic solver here. Annealing edits two
cells at a time, so its board shimmers. A child here can differ from the
displayed board across several boxes at once, so the board lurches whenever
evolution finds something better.

It is also, honestly, a bad way to solve Sudoku, which is the point of
having it. Crossover assumes good "genes" can be recombined into a better
whole, but a Sudoku box that is locally fine can still be globally wrong,
so mixing two decent parents routinely produces a worse child. Evolution
then reliably stalls one or two digits short, where every single mutation
scores worse than standing still and there is no gradient left to climb.
Expect it to fail on anything but easy puzzles.

Only improvements are traced. Evaluating a whole population per generation
would mean tens of thousands of steps nobody can read, so a step is emitted
only when a new best organism appears, as the diff between it and the board
currently on screen."""

import random
import time

from app.core import Board, SolveResult, SolveStats, SolveStep
from app.core.schemas import GRID_SIZE
from app.solvers.base import register

BOX_SIZE = 3
POPULATION_SIZE = 140
# Kept deliberately modest. Population and generation counts several times
# these were measured, and they do not rescue it: it stalls 2-6 conflicts
# short at every budget tried, so the extra seconds bought nothing except a
# slower page. See the note on premature convergence above.
MAX_GENERATIONS = 400
ELITE_COUNT = 8
TOURNAMENT_SIZE = 5
# Applied per box, so a child usually picks up one or two swaps rather than
# at most one across the whole grid.
BOX_MUTATION_RATE = 0.20
# Once the population goes homogeneous no amount of breeding recovers it, so
# reseed around the best organism instead of burning the remaining budget.
RESTART_AFTER_STALE_GENERATIONS = 60
SEED = 0

Cell = tuple[int, int]
Grid = list[list[int]]


def _box_cells(box_index: int) -> list[Cell]:
    r0 = (box_index // BOX_SIZE) * BOX_SIZE
    c0 = (box_index % BOX_SIZE) * BOX_SIZE
    return [(r, c) for r in range(r0, r0 + BOX_SIZE) for c in range(c0, c0 + BOX_SIZE)]


BOXES = [_box_cells(i) for i in range(GRID_SIZE)]


def _fitness(grid: Grid) -> int:
    """Row and column conflicts. Boxes are valid by construction, so 0 here
    means the grid is a complete solution.

    Every line holds exactly 9 values, so the number of duplicates in it is
    just 9 minus the number of distinct ones. This runs on the order of a
    hundred thousand times per solve, so it is worth not counting by hand."""
    conflicts = 0
    for i in range(GRID_SIZE):
        conflicts += GRID_SIZE - len(set(grid[i]))
        conflicts += GRID_SIZE - len({grid[r][i] for r in range(GRID_SIZE)})
    return conflicts


class GeneticSolver:
    name = "genetic"

    def solve(self, board: Board) -> SolveResult:
        given_mask = [[value != 0 for value in row] for row in board.cells]
        given_count = sum(1 for row in given_mask for is_given in row if is_given)
        # Cells each box is free to shuffle, precomputed once.
        free_cells = [[(r, c) for r, c in box if not given_mask[r][c]] for box in BOXES]

        rng = random.Random(SEED)
        steps: list[SolveStep] = []
        displayed = [row[:] for row in board.cells]

        start = time.perf_counter()
        best = self._evolve(board.cells, free_cells, rng, steps, displayed)
        elapsed = time.perf_counter() - start

        return SolveResult(
            solved=_fitness(best) == 0,
            solved_board=Board(cells=best),
            steps=steps,
            stats=SolveStats(
                algorithm=self.name,
                elapsed_time=elapsed,
                step_count=len(steps),
                given_count=given_count,
            ),
        )

    def _evolve(
        self,
        puzzle: Grid,
        free_cells: list[list[Cell]],
        rng: random.Random,
        steps: list[SolveStep],
        displayed: Grid,
    ) -> Grid:
        # Organisms are carried as (fitness, grid). Scoring is by far the
        # hottest operation here, and selection alone would otherwise
        # re-derive it thousands of times per generation for grids that
        # haven't changed.
        def spawn() -> tuple[int, Grid]:
            grid = self._random_organism(puzzle, free_cells, rng)
            return _fitness(grid), grid

        population = [spawn() for _ in range(POPULATION_SIZE)]
        best_fitness, best = min(population, key=lambda scored: scored[0])
        best = [row[:] for row in best]
        self._record_improvement(best, 0, best_fitness, steps, displayed)
        stale = 0

        for generation in range(1, MAX_GENERATIONS + 1):
            if best_fitness == 0:
                break

            population.sort(key=lambda scored: scored[0])
            if population[0][0] < best_fitness:
                best_fitness, fittest = population[0]
                best = [row[:] for row in fittest]
                self._record_improvement(best, generation, best_fitness, steps, displayed)
                stale = 0
            else:
                stale += 1

            if stale >= RESTART_AFTER_STALE_GENERATIONS:
                population = [spawn() for _ in range(POPULATION_SIZE)]
                population[0] = (best_fitness, [row[:] for row in best])
                stale = 0
                continue

            next_population = [
                (score, [row[:] for row in grid]) for score, grid in population[:ELITE_COUNT]
            ]
            while len(next_population) < POPULATION_SIZE:
                parent_a = self._tournament(population, rng)
                parent_b = self._tournament(population, rng)
                child = self._crossover(parent_a, parent_b, rng)
                self._mutate(child, free_cells, rng)
                next_population.append((_fitness(child), child))
            population = next_population

        return best

    @staticmethod
    def _random_organism(puzzle: Grid, free_cells: list[list[Cell]], rng: random.Random) -> Grid:
        grid = [row[:] for row in puzzle]
        for box_index, box in enumerate(BOXES):
            present = {grid[r][c] for r, c in box if grid[r][c] != 0}
            missing = [value for value in range(1, 10) if value not in present]
            rng.shuffle(missing)
            for (r, c), value in zip(free_cells[box_index], missing):
                grid[r][c] = value
        return grid

    @staticmethod
    def _tournament(population: list[tuple[int, Grid]], rng: random.Random) -> Grid:
        contenders = rng.sample(population, TOURNAMENT_SIZE)
        return min(contenders, key=lambda scored: scored[0])[1]

    @staticmethod
    def _crossover(parent_a: Grid, parent_b: Grid, rng: random.Random) -> Grid:
        """Inherit each 3x3 box whole from one parent or the other. Taking
        partial boxes would break the one-of-each-digit invariant that makes
        every organism box-valid."""
        child = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        for box in BOXES:
            source = parent_a if rng.random() < 0.5 else parent_b
            for r, c in box:
                child[r][c] = source[r][c]
        return child

    @staticmethod
    def _mutate(grid: Grid, free_cells: list[list[Cell]], rng: random.Random) -> None:
        """Swap two non-given cells within a box, considered box by box.
        Swapping inside a box is the only move that preserves the
        one-of-each-digit invariant every organism is built on."""
        for box in free_cells:
            if len(box) >= 2 and rng.random() < BOX_MUTATION_RATE:
                (r1, c1), (r2, c2) = rng.sample(box, 2)
                grid[r1][c1], grid[r2][c2] = grid[r2][c2], grid[r1][c1]

    @staticmethod
    def _record_improvement(
        organism: Grid, generation: int, fitness: int, steps: list[SolveStep], displayed: Grid
    ) -> None:
        """Trace only what changed between the board on screen and the new
        best organism, so the visualizer shows evolution's progress rather
        than every candidate it considered."""
        reasoning = f"generation {generation}, {fitness} conflicts left"
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if displayed[r][c] == organism[r][c]:
                    continue
                displayed[r][c] = organism[r][c]
                steps.append(
                    SolveStep(
                        action="place", cell=(r, c), value=organism[r][c], reasoning=reasoning
                    )
                )


register(GeneticSolver())
