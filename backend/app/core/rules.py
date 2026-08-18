"""Shared Sudoku rule checks. Every solver needs these — kept here once
instead of reimplemented per-algorithm."""

from app.core.schemas import GRID_SIZE

BOX_SIZE = 3


def box_start(index: int) -> int:
    return (index // BOX_SIZE) * BOX_SIZE


def is_valid_placement(cells: list[list[int]], row: int, col: int, value: int) -> bool:
    """Whether `value` can legally go at (row, col), ignoring whatever is
    currently there."""
    for i in range(GRID_SIZE):
        if i != col and cells[row][i] == value:
            return False
        if i != row and cells[i][col] == value:
            return False

    box_row, box_col = box_start(row), box_start(col)
    for r in range(box_row, box_row + BOX_SIZE):
        for c in range(box_col, box_col + BOX_SIZE):
            if (r, c) != (row, col) and cells[r][c] == value:
                return False

    return True


def is_complete(cells: list[list[int]]) -> bool:
    return all(value != 0 for row in cells for value in row)


def is_valid_board(cells: list[list[int]]) -> bool:
    """Whether every filled cell is consistent with Sudoku's rules."""
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            value = cells[row][col]
            if value != 0 and not is_valid_placement(cells, row, col, value):
                return False
    return True
