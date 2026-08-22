from app.core import Board, is_complete, is_valid_board
from app.ml.algorithm_features import CANDIDATES
from app.solvers import get_solver
from tests.test_backtracking import EASY, HARD, apply_steps


def _solver():
    return get_solver("algorithm_picker")


def test_registers_under_expected_name() -> None:
    assert _solver().name == "algorithm_picker"


def test_always_solves() -> None:
    """Every candidate it can delegate to is a complete solver, so unlike
    simulated annealing or the neural net, this one has no honest excuse
    to fail."""
    for puzzle in (EASY, HARD):
        result = _solver().solve(Board(cells=puzzle))
        assert result.solved is True
        assert is_complete(result.solved_board.cells)
        assert is_valid_board(result.solved_board.cells)


def test_stats_report_which_algorithm_it_picked() -> None:
    for puzzle in (EASY, HARD):
        result = _solver().solve(Board(cells=puzzle))
        assert result.stats.algorithm.startswith("algorithm_picker -> ")
        picked = result.stats.algorithm.removeprefix("algorithm_picker -> ")
        assert picked in CANDIDATES


def test_never_picks_an_incomplete_algorithm() -> None:
    """The picker is only ever trained to choose among the three complete
    solvers — routing to simulated annealing or the neural net would
    silently reintroduce the chance of not solving at all, defeating the
    point of picking a "fastest reliable" algorithm."""
    for puzzle in (EASY, HARD):
        result = _solver().solve(Board(cells=puzzle))
        picked = result.stats.algorithm.removeprefix("algorithm_picker -> ")
        assert picked not in ("simulated_annealing", "neural_net")


def test_given_cells_are_never_overwritten() -> None:
    for puzzle in (EASY, HARD):
        result = _solver().solve(Board(cells=puzzle))
        for row in range(9):
            for col in range(9):
                given = puzzle[row][col]
                if given != 0:
                    assert result.solved_board.cells[row][col] == given


def test_replaying_steps_reproduces_solved_board() -> None:
    """Steps come straight from whichever solver it delegated to, so this
    should hold exactly like it does for that solver's own tests."""
    for puzzle in (EASY, HARD):
        result = _solver().solve(Board(cells=puzzle))
        replayed = apply_steps(puzzle, result.steps)
        assert replayed == result.solved_board.cells
