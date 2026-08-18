"""Dancing Links (Knuth's Algorithm X) — Sudoku recast as an exact cover
problem: 729 candidate (row, col, value) choices, each satisfying exactly 4
of 324 constraints (one cell filled, one value per row, one per column, one
per box). Search always branches on the least-satisfiable constraint left,
which tends to explore cells in a very different order than raster-order
backtracking or cell-by-cell constraint propagation."""

import time

from app.core import Board, SolveResult, SolveStats, SolveStep
from app.core.schemas import GRID_SIZE
from app.solvers.base import register

BOX_SIZE = 3
NUM_CONSTRAINTS = GRID_SIZE * GRID_SIZE * 4
RowId = tuple[int, int, int]


class _Node:
    __slots__ = ("left", "right", "up", "down", "column", "row_id")

    def __init__(self) -> None:
        self.left: _Node = self
        self.right: _Node = self
        self.up: _Node = self
        self.down: _Node = self
        self.column: _Column = None  # type: ignore[assignment]
        self.row_id: RowId | None = None


class _Column(_Node):
    __slots__ = ("size",)

    def __init__(self) -> None:
        super().__init__()
        self.column = self
        self.size = 0


def _constraint_indices(row: int, col: int, value: int) -> tuple[int, int, int, int]:
    n2 = GRID_SIZE * GRID_SIZE
    box = (row // BOX_SIZE) * BOX_SIZE + (col // BOX_SIZE)
    cell = row * GRID_SIZE + col
    row_constraint = n2 + row * GRID_SIZE + (value - 1)
    col_constraint = 2 * n2 + col * GRID_SIZE + (value - 1)
    box_constraint = 3 * n2 + box * GRID_SIZE + (value - 1)
    return cell, row_constraint, col_constraint, box_constraint


class _DLXMatrix:
    def __init__(self) -> None:
        self.header = _Column()
        self.columns: list[_Column] = []
        for _ in range(NUM_CONSTRAINTS):
            column = _Column()
            column.left = self.header.left
            column.right = self.header
            self.header.left.right = column
            self.header.left = column
            self.columns.append(column)

        self.rows: dict[RowId, list[_Node]] = {}
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                for value in range(1, 10):
                    self._add_row(row, col, value)

    def _add_row(self, row: int, col: int, value: int) -> None:
        nodes: list[_Node] = []
        prev: _Node | None = None
        for index in _constraint_indices(row, col, value):
            column = self.columns[index]
            node = _Node()
            node.row_id = (row, col, value)
            node.column = column
            node.up = column.up
            node.down = column
            column.up.down = node
            column.up = node
            column.size += 1

            if prev is None:
                node.left = node.right = node
            else:
                node.left = prev
                node.right = prev.right
                prev.right.left = node
                prev.right = node
            prev = node
            nodes.append(node)
        self.rows[(row, col, value)] = nodes

    @staticmethod
    def cover(column: _Column) -> None:
        column.right.left = column.left
        column.left.right = column.right
        node = column.down
        while node is not column:
            right = node.right
            while right is not node:
                right.down.up = right.up
                right.up.down = right.down
                right.column.size -= 1
                right = right.right
            node = node.down

    @staticmethod
    def uncover(column: _Column) -> None:
        node = column.up
        while node is not column:
            left = node.left
            while left is not node:
                left.column.size += 1
                left.down.up = left
                left.up.down = left
                left = left.left
            node = node.up
        column.right.left = column
        column.left.right = column

    def cover_given(self, row: int, col: int, value: int) -> None:
        """Lock in a clue by covering all 4 constraints it satisfies —
        equivalent to Algorithm X choosing this row before search begins."""
        for node in self.rows[(row, col, value)]:
            self.cover(node.column)

    def _choose_column(self) -> _Column:
        best: _Column | None = None
        column = self.header.right
        while column is not self.header:
            assert isinstance(column, _Column)
            if best is None or column.size < best.size:
                best = column
            column = column.right
        assert best is not None
        return best

    def search(self, steps: list[SolveStep]) -> bool:
        if self.header.right is self.header:
            return True

        column = self._choose_column()
        if column.size == 0:
            return False

        self.cover(column)

        node = column.down
        while node is not column:
            assert node.row_id is not None
            row, col, value = node.row_id

            right = node.right
            while right is not node:
                self.cover(right.column)
                right = right.right

            steps.append(SolveStep(action="place", cell=(row, col), value=value))

            if self.search(steps):
                return True

            steps.append(SolveStep(action="remove", cell=(row, col), value=value))

            left = node.left
            while left is not node:
                self.uncover(left.column)
                left = left.left

            node = node.down

        self.uncover(column)
        return False


class DancingLinksSolver:
    name = "dancing_links"

    def solve(self, board: Board) -> SolveResult:
        cells = [row[:] for row in board.cells]
        given_count = sum(1 for row in cells for value in row if value != 0)

        matrix = _DLXMatrix()
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                value = cells[row][col]
                if value != 0:
                    matrix.cover_given(row, col, value)

        steps: list[SolveStep] = []
        start = time.perf_counter()
        solved = matrix.search(steps)
        elapsed = time.perf_counter() - start

        for step in steps:
            row, col = step.cell
            cells[row][col] = step.value if step.action == "place" else 0

        return SolveResult(
            solved=solved,
            solved_board=Board(cells=cells),
            steps=steps,
            stats=SolveStats(
                algorithm=self.name,
                elapsed_time=elapsed,
                step_count=len(steps),
                given_count=given_count,
            ),
        )


register(DancingLinksSolver())
