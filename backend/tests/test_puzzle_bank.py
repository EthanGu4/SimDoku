from app.core.puzzle_bank import get_puzzles, get_random_puzzle
from app.core.rules import is_valid_board

DIFFICULTIES = ("easy", "medium", "hard")


def test_each_difficulty_has_a_hundred_puzzles() -> None:
    for difficulty in DIFFICULTIES:
        assert len(get_puzzles(difficulty)) == 100


def test_puzzle_ids_are_unique_within_a_difficulty() -> None:
    for difficulty in DIFFICULTIES:
        ids = [p.id for p in get_puzzles(difficulty)]
        assert len(ids) == len(set(ids))


def test_puzzles_and_solutions_are_rule_valid() -> None:
    for difficulty in DIFFICULTIES:
        for puzzle in get_puzzles(difficulty):
            assert is_valid_board(puzzle.board.cells)
            assert is_valid_board(puzzle.solution.cells)


def test_solution_agrees_with_the_given_cells() -> None:
    for difficulty in DIFFICULTIES:
        for puzzle in get_puzzles(difficulty):
            for row in range(9):
                for col in range(9):
                    given = puzzle.board.cells[row][col]
                    if given != 0:
                        assert puzzle.solution.cells[row][col] == given


def test_random_puzzle_comes_from_the_requested_difficulty() -> None:
    for difficulty in DIFFICULTIES:
        ids = {p.id for p in get_puzzles(difficulty)}
        for _ in range(10):
            assert get_random_puzzle(difficulty).id in ids
