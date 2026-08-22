from app.core import Board, is_complete, is_valid_board
from app.core.puzzle_bank import get_puzzles
from app.solvers.backtracking import BacktrackingSolver
from app.solvers.constraint_propagation import ConstraintPropagationSolver
from app.solvers.fish_patterns import FishPatternSolver
from tests.test_backtracking import EASY, HARD, apply_steps

# Puzzles from the bank that are known to exercise each pattern, so a
# regression in the fish logic fails loudly instead of quietly degrading
# this solver into plain constraint propagation.
X_WING_PUZZLE_ID = "medium-00057aae90e4"
SWORDFISH_PUZZLE_ID = "medium-000d63c5c678"


def _puzzle_by_id(puzzle_id: str):
    difficulty = puzzle_id.split("-")[0]
    return next(p for p in get_puzzles(difficulty) if p.id == puzzle_id)


def _techniques_used(result) -> list[str]:
    return [
        step.reasoning for step in result.steps if step.reasoning and "after " in step.reasoning
    ]


def test_registers_under_expected_name() -> None:
    assert FishPatternSolver().name == "x_wing_swordfish"


def test_solves_easy_and_hard_puzzles() -> None:
    for puzzle in (EASY, HARD):
        result = FishPatternSolver().solve(Board(cells=puzzle))
        assert result.solved is True
        assert is_complete(result.solved_board.cells)
        assert is_valid_board(result.solved_board.cells)


def test_replaying_steps_reproduces_solved_board() -> None:
    for puzzle in (EASY, HARD):
        result = FishPatternSolver().solve(Board(cells=puzzle))
        assert apply_steps(puzzle, result.steps) == result.solved_board.cells


def test_given_cells_are_never_overwritten() -> None:
    for puzzle in (EASY, HARD):
        result = FishPatternSolver().solve(Board(cells=puzzle))
        for row in range(9):
            for col in range(9):
                if puzzle[row][col] != 0:
                    assert result.solved_board.cells[row][col] == puzzle[row][col]


def test_agrees_with_backtracking_on_the_unique_solution() -> None:
    for puzzle in (EASY, HARD):
        assert (
            FishPatternSolver().solve(Board(cells=puzzle)).solved_board.cells
            == BacktrackingSolver().solve(Board(cells=puzzle)).solved_board.cells
        )


def test_x_wing_actually_fires_and_still_solves_correctly() -> None:
    puzzle = _puzzle_by_id(X_WING_PUZZLE_ID)
    result = FishPatternSolver().solve(puzzle.board)

    assert any("X-Wing" in technique for technique in _techniques_used(result))
    assert result.solved_board.cells == puzzle.solution.cells


def test_swordfish_actually_fires_and_still_solves_correctly() -> None:
    puzzle = _puzzle_by_id(SWORDFISH_PUZZLE_ID)
    result = FishPatternSolver().solve(puzzle.board)

    assert any("Swordfish" in technique for technique in _techniques_used(result))
    assert result.solved_board.cells == puzzle.solution.cells


def test_matches_constraint_propagation_when_no_pattern_fires() -> None:
    """The two solvers share their naked/hidden single logic, so on a puzzle
    where no fish pattern applies they must produce an identical trace.
    Without this, a difference in deduction order would masquerade as a
    benefit (or cost) of the fish patterns in the comparison view."""
    checked = 0
    for puzzle in get_puzzles("easy")[:25]:
        fish_result = FishPatternSolver().solve(puzzle.board)
        if _techniques_used(fish_result):
            continue
        cp_result = ConstraintPropagationSolver().solve(puzzle.board)
        assert len(fish_result.steps) == len(cp_result.steps)
        checked += 1

    assert checked > 0, "no fish-free puzzles in the sample, test proved nothing"
