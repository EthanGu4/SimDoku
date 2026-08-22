"""Trains the algorithm picker (Phase 6): for every puzzle in the race
dataset, runs each complete solver (backtracking, constraint_propagation,
dancing_links) with a wall-clock cap, labels the puzzle with whichever was
fastest, and fits a small decision tree on a few structural features
(app.ml.algorithm_features). Weights are committed; this is a dev-time
tool, not run at request time.

Trains on-demand from the race dataset rather than from persisted run
history, since race mode is stateless by design (see CLAUDE.md).

The race dataset alone turned out to have almost no label diversity:
dancing_links' O(1) backtrack makes it fastest on nearly every puzzle in
that set (296/300 in an early run), which starved the other two candidates
of training examples. The gap is puzzles solvable almost entirely by naked
and hidden singles, where constraint_propagation's near-zero search cost
beats dancing_links' fixed exact-cover setup cost — the race dataset's
"easy" bucket (Sukaku Explainer rating < 1.5) still isn't that easy. So
this also generates synthetic puzzles spanning a much wider given-count
range (same randomized-backtracking generator as
scripts/import_race_puzzles.py, no external dataset) specifically to
surface those cases.

Usage (from backend/, with the venv active):
    python -m scripts.train_algorithm_picker
"""

import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402
from sklearn.tree import DecisionTreeClassifier  # noqa: E402

from app.core.race_puzzles import Difficulty, get_race_puzzles  # noqa: E402
from app.core.rules import is_valid_placement  # noqa: E402
from app.core.schemas import GRID_SIZE, Board  # noqa: E402
from app.core.timeout import solve_with_timeout  # noqa: E402
from app.ml.algorithm_features import CANDIDATES, WEIGHTS_PATH, extract_features  # noqa: E402
from app.solvers.backtracking import BacktrackingSolver  # noqa: E402
from app.solvers.constraint_propagation import ConstraintPropagationSolver  # noqa: E402
from app.solvers.dancing_links import DancingLinksSolver  # noqa: E402

SOLVE_TIME_CAP_SECONDS = 2.0
DIFFICULTIES: tuple[Difficulty, ...] = ("easy", "medium", "hard")
SYNTHETIC_GIVEN_COUNTS = [35, 40, 45, 50, 55, 60, 65, 70, 75, 78]
SYNTHETIC_BOARDS_PER_LEVEL = 15
MAX_TREE_DEPTH = 4
VAL_FRACTION = 0.2
SEED = 0

SOLVERS = {
    "backtracking": BacktrackingSolver(),
    "constraint_propagation": ConstraintPropagationSolver(),
    "dancing_links": DancingLinksSolver(),
}


def _generate_solved_board(rng: random.Random) -> list[list[int]]:
    cells = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
    _fill(cells, rng)
    return cells


def _fill(cells: list[list[int]], rng: random.Random) -> bool:
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if cells[row][col] != 0:
                continue
            candidates = list(range(1, 10))
            rng.shuffle(candidates)
            for value in candidates:
                if is_valid_placement(cells, row, col, value):
                    cells[row][col] = value
                    if _fill(cells, rng):
                        return True
                    cells[row][col] = 0
            return False
    return True


def _synthetic_puzzles(rng: random.Random) -> list[list[list[int]]]:
    puzzles = []
    for keep in SYNTHETIC_GIVEN_COUNTS:
        for _ in range(SYNTHETIC_BOARDS_PER_LEVEL):
            solved = _generate_solved_board(rng)
            positions = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)]
            rng.shuffle(positions)
            keep_set = set(positions[:keep])
            puzzles.append(
                [
                    [solved[r][c] if (r, c) in keep_set else 0 for c in range(GRID_SIZE)]
                    for r in range(GRID_SIZE)
                ]
            )
    return puzzles


def _label_puzzle(cells: list[list[int]]) -> str | None:
    board = Board(cells=cells)
    timings: dict[str, float] = {}
    for name, solver in SOLVERS.items():
        result = solve_with_timeout(solver, board, SOLVE_TIME_CAP_SECONDS)
        if result is not None and result.solved:
            timings[name] = result.stats.elapsed_time
    if not timings:
        return None
    return min(timings, key=lambda name: timings[name])


def build_dataset() -> tuple[list[list[float]], list[str]]:
    features: list[list[float]] = []
    labels: list[str] = []

    for difficulty in DIFFICULTIES:
        puzzles = get_race_puzzles(difficulty)
        print(f"timing {len(puzzles)} {difficulty} puzzles against {list(SOLVERS)}...")
        for puzzle in puzzles:
            fastest = _label_puzzle(puzzle.board.cells)
            if fastest is None:
                # Shouldn't happen — all three candidates are complete —
                # but skip defensively rather than mislabel.
                print(f"  WARNING: {puzzle.id} — no candidate solved it in time, skipping")
                continue
            features.append(extract_features(puzzle.board.cells))
            labels.append(fastest)

    synthetic = _synthetic_puzzles(random.Random(SEED))
    print(f"timing {len(synthetic)} synthetic puzzles (given counts {SYNTHETIC_GIVEN_COUNTS})...")
    for cells in synthetic:
        fastest = _label_puzzle(cells)
        if fastest is None:
            continue
        features.append(extract_features(cells))
        labels.append(fastest)

    return features, labels


def main() -> None:
    features, labels = build_dataset()
    print(f"{len(features)} labeled examples")
    print("label distribution:", dict(Counter(labels)))
    assert set(labels) <= set(CANDIDATES)

    # Stratifying needs at least 2 examples of every class — fall back to a
    # plain split if a class is still too rare even after augmentation.
    rarest_class_count = min(Counter(labels).values())
    stratify = labels if rarest_class_count >= 2 else None
    X_train, X_val, y_train, y_val = train_test_split(
        features, labels, test_size=VAL_FRACTION, random_state=SEED, stratify=stratify
    )

    model = DecisionTreeClassifier(max_depth=MAX_TREE_DEPTH, random_state=SEED)
    model.fit(X_train, y_train)

    val_accuracy = model.score(X_val, y_val)
    print(f"validation accuracy: {val_accuracy:.3f}")

    WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, WEIGHTS_PATH)
    print(f"saved model to {WEIGHTS_PATH}")


if __name__ == "__main__":
    main()
