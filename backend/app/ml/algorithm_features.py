"""Structural features extracted from a puzzle, shared by the algorithm
picker (inference) and its training script. Kept import-side-effect-free —
unlike algorithm_picker.py, importing this never touches the solver
registry or requires a trained model to already exist on disk.

Only the three *complete* solvers are candidates for picking. Simulated
annealing and the neural net have no completeness guarantee (see their own
docstrings) — a "picker" that might route to an algorithm known to
sometimes not solve at all would undermine the whole point of picking."""

from pathlib import Path

from app.core.rules import is_valid_placement
from app.core.schemas import GRID_SIZE

WEIGHTS_PATH = Path(__file__).parent / "weights" / "algorithm_picker.joblib"
CANDIDATES = ["backtracking", "constraint_propagation", "dancing_links"]

FEATURE_NAMES = ["given_count", "avg_candidates", "min_candidates", "max_candidates"]


def extract_features(cells: list[list[int]]) -> list[float]:
    given_count = sum(1 for row in cells for value in row if value != 0)
    candidate_counts = [
        sum(1 for value in range(1, 10) if is_valid_placement(cells, row, col, value))
        for row in range(GRID_SIZE)
        for col in range(GRID_SIZE)
        if cells[row][col] == 0
    ]
    return [
        float(given_count),
        sum(candidate_counts) / len(candidate_counts),
        float(min(candidate_counts)),
        float(max(candidate_counts)),
    ]
