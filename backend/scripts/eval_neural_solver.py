"""Measures the neural solver's real solve rate on puzzles it has never
seen, broken down by difficulty.

Training draws the first PUZZLES_PER_FILE lines of each source file, so this
evaluates on lines *after* that cutoff. The committed puzzle bank is not a
valid test set here: it is drawn from the head of the same files and is
therefore inside the training data.

Usage (from backend/, with the venv active):
    python -m scripts.eval_neural_solver [weights.pt ...]
"""

import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.schemas import Board  # noqa: E402
from app.ml.sudoku_cnn import (  # noqa: E402
    WEIGHTS_PATH,
    SudokuCNN,
    most_confident_valid_placement,
    predict,
)
from app.solvers.dancing_links import DancingLinksSolver  # noqa: E402
from scripts.train_neural_solver import CACHE_DIR, PUZZLES_PER_FILE, to_cells  # noqa: E402

TEST_PUZZLES_PER_DIFFICULTY = 100


def load_unseen() -> dict[str, list[tuple[list[list[int]], list[list[int]]]]]:
    if not (CACHE_DIR / "easy.txt").exists():
        sys.exit(
            "No puzzle cache found. Run `python -m scripts.train_neural_solver` first;\n"
            "it downloads the source files this evaluates against."
        )

    solver = DancingLinksSolver()
    by_difficulty = {}
    for name in ("easy", "medium", "hard"):
        lines = (CACHE_DIR / f"{name}.txt").read_text().splitlines()
        unseen = lines[PUZZLES_PER_FILE : PUZZLES_PER_FILE + TEST_PUZZLES_PER_DIFFICULTY]
        pairs = []
        for line in unseen:
            cells = to_cells(line.split()[1])
            result = solver.solve(Board(cells=cells))
            if result.solved:
                pairs.append((cells, result.solved_board.cells))
        by_difficulty[name] = pairs
    return by_difficulty


def evaluate(model: torch.nn.Module, pairs) -> tuple[int, float]:
    solved = 0
    filled_total = 0.0
    for puzzle, solution in pairs:
        cells = [row[:] for row in puzzle]
        while any(0 in row for row in cells):
            best = most_confident_valid_placement(cells, predict(model, cells))
            if best is None:
                break
            _, r, c, value = best
            cells[r][c] = value
        if cells == solution:
            solved += 1
        filled_total += sum(1 for row in cells for v in row if v != 0) / 81
    return solved, filled_total / len(pairs)


def main() -> None:
    checkpoints = [Path(p) for p in sys.argv[1:]] or [WEIGHTS_PATH]
    data = load_unseen()
    print(f"test set: {', '.join(f'{k}={len(v)}' for k, v in data.items())} (unseen by training)\n")

    for path in checkpoints:
        model = SudokuCNN()
        model.load_state_dict(torch.load(path, map_location="cpu"))
        model.eval()
        print(f"{path.name}")
        total_solved = total_count = 0
        for difficulty, pairs in data.items():
            solved, filled = evaluate(model, pairs)
            total_solved += solved
            total_count += len(pairs)
            print(
                f"  {difficulty:7s} {solved:3d}/{len(pairs):<3d} solved   avg filled {filled:.1%}"
            )
        rate = total_solved / total_count
        print(f"  {'overall':7s} {total_solved:3d}/{total_count:<3d} = {rate:.0%}\n")


if __name__ == "__main__":
    main()
