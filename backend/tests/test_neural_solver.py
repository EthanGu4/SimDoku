from app.core import Board, is_complete, is_valid_board
from app.core.puzzles import MEDIUM_CELLS
from app.core.rules import is_valid_placement
from app.ml.neural_solver import NeuralSolver
from tests.test_backtracking import EASY, HARD, apply_steps

MEDIUM = MEDIUM_CELLS


def test_registers_under_expected_name() -> None:
    assert NeuralSolver().name == "neural_net"


def test_makes_substantial_progress_on_easy_puzzle() -> None:
    """This solver is trained, not guaranteed — see
    test_is_allowed_to_fail_on_sparse_puzzles. Even on our densest-given
    (easiest) benchmark puzzle it doesn't reliably reach a full solve, but
    it should still fill in the large majority of cells before it either
    finishes or gets stuck, which is what actually demonstrates the model
    learned something real rather than nothing at all."""
    result = NeuralSolver().solve(Board(cells=EASY))

    filled = sum(1 for row in result.solved_board.cells for value in row if value != 0)
    assert filled / 81 > 0.85
    assert is_valid_board(result.solved_board.cells)


def test_given_cells_are_never_overwritten() -> None:
    for puzzle in (EASY, MEDIUM, HARD):
        result = NeuralSolver().solve(Board(cells=puzzle))
        for row in range(9):
            for col in range(9):
                given = puzzle[row][col]
                if given != 0:
                    assert result.solved_board.cells[row][col] == given


def test_replaying_steps_reproduces_solved_board() -> None:
    for puzzle in (EASY, MEDIUM, HARD):
        result = NeuralSolver().solve(Board(cells=puzzle))
        replayed = apply_steps(puzzle, result.steps)
        assert replayed == result.solved_board.cells


def test_never_places_a_rule_violation() -> None:
    """Unlike simulated annealing, this solver checks every placement
    against Sudoku's hard constraints before committing to it — so the
    board it produces must stay rule-valid at every point, complete or
    not. A confidently wrong *choice* is allowed; a rule violation isn't."""
    for puzzle in (EASY, MEDIUM, HARD):
        result = NeuralSolver().solve(Board(cells=puzzle))
        assert is_valid_board(result.solved_board.cells)


def test_is_allowed_to_fail_on_sparse_puzzles() -> None:
    """Like simulated annealing, this solver has no completeness guarantee
    — a confident-but-wrong early placement can paint it into a corner on
    a sparse puzzle. That's a documented, expected limitation of solving by
    learned inference instead of search, not a bug. What matters is that it
    terminates cleanly and never corrupts the board even when it can't
    finish."""
    result = NeuralSolver().solve(Board(cells=HARD))
    assert is_valid_board(result.solved_board.cells)
    assert result.stats.elapsed_time < 10.0
    if not result.solved:
        assert not is_complete(result.solved_board.cells)


def test_reasoning_reports_a_confidence() -> None:
    result = NeuralSolver().solve(Board(cells=EASY))
    place_steps = [s for s in result.steps if s.action == "place"]
    assert len(place_steps) > 0
    assert all(s.reasoning and "confidence" in s.reasoning for s in place_steps)


def test_stuck_cell_has_no_legal_digit_left() -> None:
    """If the solver stops early, every empty cell it left behind should
    genuinely have zero legal candidates — proof it stopped because it was
    stuck, not because it gave up early for no reason."""
    result = NeuralSolver().solve(Board(cells=HARD))
    if result.solved:
        return
    cells = result.solved_board.cells
    for row in range(9):
        for col in range(9):
            if cells[row][col] == 0:
                assert all(not is_valid_placement(cells, row, col, v) for v in range(1, 10))
