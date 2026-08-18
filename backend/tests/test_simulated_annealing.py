from app.core import is_complete, is_valid_board
from app.core.schemas import Board
from app.solvers.simulated_annealing import SimulatedAnnealingSolver
from tests.test_backtracking import EASY, HARD, apply_steps


def _box_values(cells: list[list[int]], box_row: int, box_col: int) -> list[int]:
    r0, c0 = box_row * 3, box_col * 3
    return [cells[r][c] for r in range(r0, r0 + 3) for c in range(c0, c0 + 3)]


def test_registers_under_expected_name() -> None:
    assert SimulatedAnnealingSolver().name == "simulated_annealing"


def test_solves_easy_puzzle() -> None:
    result = SimulatedAnnealingSolver().solve(Board(cells=EASY))

    assert result.solved is True
    assert is_complete(result.solved_board.cells)
    assert is_valid_board(result.solved_board.cells)
    assert result.stats.elapsed_time < 5.0


def test_given_cells_are_never_overwritten() -> None:
    for puzzle in (EASY, HARD):
        result = SimulatedAnnealingSolver().solve(Board(cells=puzzle))
        for row in range(9):
            for col in range(9):
                given = puzzle[row][col]
                if given != 0:
                    assert result.solved_board.cells[row][col] == given


def test_replaying_steps_reproduces_solved_board() -> None:
    for puzzle in (EASY, HARD):
        result = SimulatedAnnealingSolver().solve(Board(cells=puzzle))
        replayed = apply_steps(puzzle, result.steps)
        assert replayed == result.solved_board.cells


def test_box_constraints_hold_even_when_it_fails_to_fully_solve() -> None:
    """Swaps are always within a box, so box validity is an invariant of
    the algorithm's design regardless of whether it converges — this is
    the property that lets it get away with never checking box conflicts."""
    result = SimulatedAnnealingSolver().solve(Board(cells=HARD))
    for box_row in range(3):
        for box_col in range(3):
            values = _box_values(result.solved_board.cells, box_row, box_col)
            assert sorted(values) == list(range(1, 10))


def test_is_a_stochastic_heuristic_not_guaranteed_to_solve() -> None:
    """Unlike the other solvers, this one is allowed to fail — it's a
    documented limitation of simulated annealing on sparse puzzles, not a
    bug. What matters is that it terminates cleanly and never corrupts the
    board even when it doesn't converge."""
    result = SimulatedAnnealingSolver().solve(Board(cells=HARD))
    assert is_complete(result.solved_board.cells)
    assert result.stats.elapsed_time < 5.0
    if not result.solved:
        assert not is_valid_board(result.solved_board.cells)
