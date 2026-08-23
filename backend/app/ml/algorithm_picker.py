"""Phase 6: a "pseudo-solver" that doesn't solve anything itself — it
extracts a few structural features from the puzzle, uses a small classifier
(trained offline on the race dataset — see scripts/train_algorithm_picker.py)
to predict which of the three complete solvers will be fastest, and
delegates to it. The returned SolveResult is the delegate's, unmodified
except for `stats.algorithm`, which is annotated to show the pick so the
frontend visualizes it exactly like any other algorithm's real trace —
per the plug-in architecture, this required zero changes to the API,
frontend, or visualizer.

Weights are committed pretrained; this module only loads and runs
inference, it never trains at request time."""

import joblib

from app.core import Board, SolveResult
from app.core.schemas import SolveStats
from app.ml.algorithm_features import WEIGHTS_PATH, extract_features
from app.solvers.base import get_solver, register


class AlgorithmPickerSolver:
    name = "algorithm_picker"

    def __init__(self) -> None:
        self._model = None

    @property
    def model(self):
        """Loaded on first solve, for the same reason as the neural solver:
        its training script imports the registry, so loading at construction
        would mean the run had to load the model it was about to overwrite."""
        if self._model is None:
            self._model = joblib.load(WEIGHTS_PATH)
        return self._model

    def solve(self, board: Board) -> SolveResult:
        features = extract_features(board.cells)
        predicted = self.model.predict([features])[0]

        solver = get_solver(predicted)
        if solver is None:
            # Shouldn't happen — every CANDIDATES name is always registered
            # — but fall back to the one guaranteed-complete solver rather
            # than crash on a corrupted/stale model file.
            predicted = "backtracking"
            solver = get_solver(predicted)

        result = solver.solve(board)
        return result.model_copy(
            update={
                "stats": SolveStats(
                    algorithm=f"algorithm_picker -> {predicted}",
                    elapsed_time=result.stats.elapsed_time,
                    step_count=result.stats.step_count,
                    given_count=result.stats.given_count,
                )
            }
        )


register(AlgorithmPickerSolver())
