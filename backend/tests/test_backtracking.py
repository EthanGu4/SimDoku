from app.core import Board, SolveStep, is_complete, is_valid_board
from app.core.puzzles import EASY_CELLS, HARD_CELLS
from app.solvers.backtracking import BacktrackingSolver

# 0 = empty. Sourced from the fixed benchmark dataset (app/core/puzzles.py)
# so tests and the benchmark harness agree on what "easy"/"hard" mean.
EASY = EASY_CELLS
HARD = HARD_CELLS


def apply_steps(initial_cells: list[list[int]], steps: list[SolveStep]) -> list[list[int]]:
    cells = [row[:] for row in initial_cells]
    for step in steps:
        row, col = step.cell
        cells[row][col] = step.value if step.action == "place" else 0
    return cells


def test_registers_under_expected_name() -> None:
    assert BacktrackingSolver().name == "backtracking"


def test_solves_easy_puzzle() -> None:
    result = BacktrackingSolver().solve(Board(cells=EASY))

    assert result.solved is True
    assert is_complete(result.solved_board.cells)
    assert is_valid_board(result.solved_board.cells)
    assert result.stats.given_count == sum(v != 0 for row in EASY for v in row)
    assert result.stats.step_count == len(result.steps)


def test_solves_hard_puzzle() -> None:
    result = BacktrackingSolver().solve(Board(cells=HARD))

    assert result.solved is True
    assert is_complete(result.solved_board.cells)
    assert is_valid_board(result.solved_board.cells)


def test_replaying_steps_reproduces_solved_board() -> None:
    for puzzle in (EASY, HARD):
        result = BacktrackingSolver().solve(Board(cells=puzzle))
        replayed = apply_steps(puzzle, result.steps)
        assert replayed == result.solved_board.cells


def test_given_cells_are_never_overwritten() -> None:
    result = BacktrackingSolver().solve(Board(cells=EASY))
    for row in range(9):
        for col in range(9):
            given = EASY[row][col]
            if given != 0:
                assert result.solved_board.cells[row][col] == given


def test_trace_shows_every_digit_tried_including_rejects() -> None:
    """The visualizer's whole point is showing trial-and-error, not just
    successful placements — a sparse puzzle like HARD should genuinely
    exercise rejects and backtracks, not just clean forward fills."""
    result = BacktrackingSolver().solve(Board(cells=HARD))

    place_steps = [s for s in result.steps if s.action == "place"]
    assert any(s.reasoning == "reject" for s in place_steps)
    assert any(s.reasoning == "search" for s in place_steps)

    remove_steps = [s for s in result.steps if s.action == "remove"]
    assert any(s.reasoning is None for s in remove_steps)  # undoing an instant reject
    assert any(s.reasoning == "backtrack" for s in remove_steps)  # undoing a real dead end
