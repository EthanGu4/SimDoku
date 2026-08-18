from app.core import Board, is_complete, is_valid_board
from app.solvers.constraint_propagation import ConstraintPropagationSolver
from tests.test_backtracking import EASY, HARD, apply_steps


def test_registers_under_expected_name() -> None:
    assert ConstraintPropagationSolver().name == "constraint_propagation"


def test_solves_easy_puzzle_mostly_by_deduction() -> None:
    result = ConstraintPropagationSolver().solve(Board(cells=EASY))

    assert result.solved is True
    assert is_complete(result.solved_board.cells)
    assert is_valid_board(result.solved_board.cells)

    reasonings = [step.reasoning or "" for step in result.steps if step.action == "place"]
    assert any(r == "naked single" or r.startswith("hidden single") for r in reasonings)


def test_solves_hard_puzzle() -> None:
    result = ConstraintPropagationSolver().solve(Board(cells=HARD))

    assert result.solved is True
    assert is_complete(result.solved_board.cells)
    assert is_valid_board(result.solved_board.cells)


def test_replaying_steps_reproduces_solved_board() -> None:
    for puzzle in (EASY, HARD):
        result = ConstraintPropagationSolver().solve(Board(cells=puzzle))
        replayed = apply_steps(puzzle, result.steps)
        assert replayed == result.solved_board.cells


def test_given_cells_are_never_overwritten() -> None:
    result = ConstraintPropagationSolver().solve(Board(cells=EASY))
    for row in range(9):
        for col in range(9):
            given = EASY[row][col]
            if given != 0:
                assert result.solved_board.cells[row][col] == given


def test_agrees_with_backtracking_on_the_unique_solution() -> None:
    from app.solvers.backtracking import BacktrackingSolver

    for puzzle in (EASY, HARD):
        cp_result = ConstraintPropagationSolver().solve(Board(cells=puzzle))
        bt_result = BacktrackingSolver().solve(Board(cells=puzzle))
        assert cp_result.solved_board.cells == bt_result.solved_board.cells
