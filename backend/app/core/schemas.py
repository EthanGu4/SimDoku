"""Board / SolveStep / SolveResult — the shared contract every solver produces.

Adding a new algorithm must never require changing these schemas. If a new
algorithm seems to need a new field, prefer generalizing `action`/`reasoning`
over special-casing it here.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

GRID_SIZE = 9

StepAction = Literal["place", "remove"]


class Board(BaseModel):
    """A 9x9 Sudoku grid. 0 marks an empty cell."""

    cells: list[list[int]] = Field(description="9 rows of 9 cells each; 0 = empty, 1-9 = filled.")

    @field_validator("cells")
    @classmethod
    def validate_grid(cls, cells: list[list[int]]) -> list[list[int]]:
        if len(cells) != GRID_SIZE:
            raise ValueError(f"board must have {GRID_SIZE} rows, got {len(cells)}")
        for row in cells:
            if len(row) != GRID_SIZE:
                raise ValueError(f"each row must have {GRID_SIZE} cells, got {len(row)}")
            for value in row:
                if not 0 <= value <= 9:
                    raise ValueError(f"cell values must be 0-9, got {value}")
        return cells


class SolveStep(BaseModel):
    """One diff in a solver's trace: a single cell placed or un-placed.

    Degenerate solvers (e.g. an ML solver that jumps straight from empty to
    solved) may return zero or one step — the visualizer must tolerate that.
    """

    action: StepAction
    cell: tuple[int, int] = Field(description="(row, col), both 0-8")
    value: int | None = Field(default=None, description="value placed/removed, 1-9")
    candidates_removed: list[int] = Field(default_factory=list)
    reasoning: str | None = None


class SolveStats(BaseModel):
    algorithm: str
    elapsed_time: float = Field(
        description="server-measured compute seconds, independent of animation speed"
    )
    step_count: int
    given_count: int = Field(description="number of non-zero cells in the input puzzle")


class SolveResult(BaseModel):
    solved: bool = Field(description="whether the returned board is a complete, valid solution")
    solved_board: Board
    steps: list[SolveStep]
    stats: SolveStats
