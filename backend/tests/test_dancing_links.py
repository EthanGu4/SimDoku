from app.core import Board, is_complete, is_valid_board
from app.solvers.backtracking import BacktrackingSolver
from app.solvers.dancing_links import DancingLinksSolver
from tests.test_backtracking import EASY, HARD, apply_steps


def test_registers_under_expected_name() -> None:
    assert DancingLinksSolver().name == "dancing_links"


def test_solves_easy_puzzle() -> None:
    result = DancingLinksSolver().solve(Board(cells=EASY))

    assert result.solved is True
    assert is_complete(result.solved_board.cells)
    assert is_valid_board(result.solved_board.cells)


def test_solves_hard_puzzle() -> None:
    result = DancingLinksSolver().solve(Board(cells=HARD))

    assert result.solved is True
    assert is_complete(result.solved_board.cells)
    assert is_valid_board(result.solved_board.cells)


def test_replaying_steps_reproduces_solved_board() -> None:
    for puzzle in (EASY, HARD):
        result = DancingLinksSolver().solve(Board(cells=puzzle))
        replayed = apply_steps(puzzle, result.steps)
        assert replayed == result.solved_board.cells


def test_given_cells_are_never_overwritten() -> None:
    result = DancingLinksSolver().solve(Board(cells=EASY))
    for row in range(9):
        for col in range(9):
            given = EASY[row][col]
            if given != 0:
                assert result.solved_board.cells[row][col] == given


def test_agrees_with_backtracking_on_the_unique_solution() -> None:
    for puzzle in (EASY, HARD):
        dlx_result = DancingLinksSolver().solve(Board(cells=puzzle))
        bt_result = BacktrackingSolver().solve(Board(cells=puzzle))
        assert dlx_result.solved_board.cells == bt_result.solved_board.cells


def test_solving_twice_does_not_share_state() -> None:
    """Each solve() call must build its own matrix — a leaked shared matrix
    would make a second solve on a different puzzle fail or corrupt."""
    solver = DancingLinksSolver()
    first = solver.solve(Board(cells=EASY))
    second = solver.solve(Board(cells=HARD))

    assert first.solved is True
    assert second.solved is True
    assert first.solved_board.cells != second.solved_board.cells
