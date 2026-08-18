from app.core import is_valid_board
from app.core.puzzles import BENCHMARK_PUZZLES, get_puzzle
from app.solvers.backtracking import BacktrackingSolver


def test_every_benchmark_puzzle_is_valid_and_solvable() -> None:
    for puzzle in BENCHMARK_PUZZLES:
        assert is_valid_board(puzzle.board.cells)
        result = BacktrackingSolver().solve(puzzle.board)
        assert result.solved is True


def test_given_count_matches_the_board() -> None:
    for puzzle in BENCHMARK_PUZZLES:
        actual = sum(1 for row in puzzle.board.cells for value in row if value != 0)
        assert puzzle.given_count == actual


def test_ids_are_unique() -> None:
    ids = [puzzle.id for puzzle in BENCHMARK_PUZZLES]
    assert len(ids) == len(set(ids))


def test_get_puzzle_looks_up_by_id() -> None:
    first = BENCHMARK_PUZZLES[0]
    assert get_puzzle(first.id) == first


def test_get_puzzle_returns_none_for_unknown_id() -> None:
    assert get_puzzle("does-not-exist") is None
