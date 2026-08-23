"""A small CNN trained to predict, for every empty cell, a probability
distribution over digits 1-9 — an "unconventional" solver in the sense that
it never deduces or searches; it just repeatedly asks a trained model which
placement it's most confident about, checks that placement against Sudoku's
hard constraints (never mutating a given, never violating a rule), and
places it. If no empty cell has any legal digit left, an earlier confident-
but-wrong guess has painted the board into a corner — like simulated
annealing, this solver is allowed to fail; it just stops and reports it
honestly instead of guaranteeing a solution the way backtracking does.

Weights are trained offline by scripts/train_neural_solver.py (synthetic
puzzles generated via randomized backtracking, no external dataset) and
committed to weights/neural_solver.pt — this module only loads and runs
inference, it never trains at request time.
"""

import time

import torch

from app.core import Board, SolveResult, SolveStats, SolveStep, is_complete
from app.ml.sudoku_cnn import (
    WEIGHTS_PATH,
    SudokuCNN,
    most_confident_valid_placement,
    predict,
)
from app.solvers.base import register


class NeuralSolver:
    name = "neural_net"

    def __init__(self) -> None:
        self._model: SudokuCNN | None = None

    @property
    def model(self) -> SudokuCNN:
        """Weights load on first solve rather than at import.

        Eager loading made the model impossible to retrain: the training
        script imports another solver, that pulls in the whole registry,
        and constructing this class then tried to load the very weights
        file the run was about to replace, failing outright whenever the
        architecture had changed. Deferring it also means a missing or
        corrupt weights file degrades this one algorithm at call time
        instead of stopping the entire app from starting."""
        if self._model is None:
            model = SudokuCNN()
            model.load_state_dict(torch.load(WEIGHTS_PATH, map_location="cpu"))
            model.eval()
            self._model = model
        return self._model

    def solve(self, board: Board) -> SolveResult:
        cells = [row[:] for row in board.cells]
        given_count = sum(1 for row in cells for value in row if value != 0)
        steps: list[SolveStep] = []

        start = time.perf_counter()
        solved = self._solve(cells, steps)
        elapsed = time.perf_counter() - start

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

    def _solve(self, cells: list[list[int]], steps: list[SolveStep]) -> bool:
        while not is_complete(cells):
            probs = predict(self.model, cells)
            best = most_confident_valid_placement(cells, probs)
            if best is None:
                return False  # some empty cell has no legal digit left — dead end

            confidence, row, col, value = best
            cells[row][col] = value
            steps.append(
                SolveStep(
                    action="place",
                    cell=(row, col),
                    value=value,
                    reasoning=f"model predicted {value} ({confidence:.0%} confidence)",
                )
            )
        return True


register(NeuralSolver())
