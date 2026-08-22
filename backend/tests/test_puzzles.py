from app.core import Board, is_valid_board
from app.core.puzzles import EASY_CELLS, HARD_CELLS, MEDIUM_CELLS
from app.solvers.backtracking import BacktrackingSolver


def test_every_fixture_puzzle_is_valid_and_solvable() -> None:
    """These back every solver's correctness battery, so a broken fixture
    would quietly invalidate a lot of other tests."""
    for cells in (EASY_CELLS, MEDIUM_CELLS, HARD_CELLS):
        assert is_valid_board(cells)
        result = BacktrackingSolver().solve(Board(cells=cells))
        assert result.solved is True


def test_fixtures_get_progressively_sparser() -> None:
    givens = [
        sum(1 for row in cells for v in row if v != 0)
        for cells in (EASY_CELLS, MEDIUM_CELLS, HARD_CELLS)
    ]
    assert givens == sorted(givens, reverse=True)
