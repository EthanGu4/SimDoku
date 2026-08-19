from app.core.race_puzzles import get_race_puzzles
from app.core.rules import is_valid_board


def test_each_difficulty_has_a_hundred_puzzles() -> None:
    for difficulty in ("easy", "medium", "hard"):
        assert len(get_race_puzzles(difficulty)) == 100


def test_puzzle_ids_are_unique_within_a_difficulty() -> None:
    for difficulty in ("easy", "medium", "hard"):
        ids = [p.id for p in get_race_puzzles(difficulty)]
        assert len(ids) == len(set(ids))


def test_puzzles_and_solutions_are_rule_valid() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for puzzle in get_race_puzzles(difficulty):
            assert is_valid_board(puzzle.board.cells)
            assert is_valid_board(puzzle.solution.cells)


def test_solution_agrees_with_the_given_cells() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for puzzle in get_race_puzzles(difficulty):
            for row in range(9):
                for col in range(9):
                    given = puzzle.board.cells[row][col]
                    if given != 0:
                        assert puzzle.solution.cells[row][col] == given
