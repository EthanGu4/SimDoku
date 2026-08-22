from app.core import Board, is_complete, is_valid_board
from app.solvers.genetic import BOXES, GeneticSolver, _fitness
from tests.test_backtracking import EASY, HARD, apply_steps


def test_registers_under_expected_name() -> None:
    assert GeneticSolver().name == "genetic"


def test_given_cells_are_never_overwritten() -> None:
    """Givens are fixed points of the representation: every operator only
    ever touches free cells, so no amount of breeding may disturb them."""
    for puzzle in (EASY, HARD):
        result = GeneticSolver().solve(Board(cells=puzzle))
        for row in range(9):
            for col in range(9):
                if puzzle[row][col] != 0:
                    assert result.solved_board.cells[row][col] == puzzle[row][col]


def test_every_box_stays_a_permutation() -> None:
    """Organisms are built one-of-each-digit per box, and crossover only
    ever takes whole boxes while mutation only swaps within one. That makes
    box validity an invariant, which is what lets fitness ignore boxes and
    count row/column conflicts alone."""
    for puzzle in (EASY, HARD):
        result = GeneticSolver().solve(Board(cells=puzzle))
        for box in BOXES:
            values = sorted(result.solved_board.cells[r][c] for r, c in box)
            assert values == list(range(1, 10))


def test_replaying_steps_reproduces_the_final_board() -> None:
    """Steps are emitted as diffs against whatever was last displayed, so a
    replay has to land exactly on the organism that was returned."""
    for puzzle in (EASY, HARD):
        result = GeneticSolver().solve(Board(cells=puzzle))
        assert apply_steps(puzzle, result.steps) == result.solved_board.cells


def test_always_returns_a_full_board_and_terminates() -> None:
    """However badly evolution goes, it has to hand back a complete grid
    within its generation budget rather than running on or returning a
    half-filled one."""
    for puzzle in (EASY, HARD):
        result = GeneticSolver().solve(Board(cells=puzzle))
        assert is_complete(result.solved_board.cells)
        assert result.stats.elapsed_time < 30.0


def test_is_allowed_to_fail_and_reports_it_honestly() -> None:
    """Like simulated annealing, this has no completeness guarantee, and in
    practice it usually stalls a few conflicts short on anything but the
    easiest puzzles. What matters is that `solved` tells the truth: it is
    only ever True when the board really is a valid solution."""
    result = GeneticSolver().solve(Board(cells=HARD))
    assert result.solved is is_valid_board(result.solved_board.cells)
    if not result.solved:
        assert _fitness(result.solved_board.cells) > 0


def test_is_deterministic_for_a_fixed_seed() -> None:
    """Seeded so the same puzzle gives the same run every time. Without it
    the comparison view would show a different step count on every reload
    of the same puzzle."""
    first = GeneticSolver().solve(Board(cells=EASY))
    second = GeneticSolver().solve(Board(cells=EASY))
    assert first.solved_board.cells == second.solved_board.cells
    assert len(first.steps) == len(second.steps)
