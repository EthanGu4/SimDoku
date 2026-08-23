"""Trains the CNN behind the `neural_net` solver and writes weights to
app/ml/weights/neural_solver.pt. A dev-time tool, not run at request time.

Why the training data is built the way it is
--------------------------------------------
The obvious approach, and the one this script used first, is to take a
randomly generated solved grid, blank out random cells, and train the
network to reconstruct the original. That caps accuracy at roughly what was
measured before (~55% per cell, never completing a puzzle), and the reason
is label noise rather than model capacity: a randomly blanked grid usually
has *many* valid completions, so the label is one arbitrary choice among
them and the network is punished for answering with a different but equally
correct grid. Measured on the old generator, the share of examples with a
unique solution was 0% at 21 and 28 givens, and only 22% at 38.

So examples here are built from real puzzles instead, which have unique
solutions by construction. Partially solved boards are then produced by
revealing *correct* cells from the known solution. Adding correct digits to
a uniquely solvable puzzle keeps it uniquely solvable, so every training
example has exactly one right answer at every fill level. It also matches
inference, where the solver sees a board that fills up as it goes.

Usage (from backend/, with the venv active):
    python -m scripts.train_neural_solver
"""

import json
import random
import sys
import time
import urllib.request
from pathlib import Path

import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.schemas import GRID_SIZE, Board  # noqa: E402
from app.ml.sudoku_cnn import (  # noqa: E402
    WEIGHTS_PATH,
    SudokuCNN,
    encode_board,
    most_confident_valid_placement,
    predict,
)
from app.solvers.dancing_links import DancingLinksSolver  # noqa: E402

SOURCE_BASE = "https://raw.githubusercontent.com/grantm/sudoku-exchange-puzzle-bank/master"
SOURCE_FILES = ("easy", "medium", "hard")
PUZZLES_PER_FILE = 7_000
# Each puzzle becomes several training boards at different fill levels.
BOARDS_PER_PUZZLE = 3
HELD_OUT_PUZZLES = 60

EPOCHS = 26
BATCH_SIZE = 256
LEARNING_RATE = 2e-3
VAL_FRACTION = 0.05
SEED = 0

CACHE_DIR = Path(__file__).resolve().parent / ".puzzle_cache"


def fetch_puzzle_digits() -> list[str]:
    """The 81-character puzzle strings, cached so repeated runs skip the
    download."""
    CACHE_DIR.mkdir(exist_ok=True)
    digits: list[str] = []
    for name in SOURCE_FILES:
        cached = CACHE_DIR / f"{name}.txt"
        if not cached.exists():
            print(f"downloading {name}.txt ...")
            with urllib.request.urlopen(f"{SOURCE_BASE}/{name}.txt") as response:
                cached.write_bytes(response.read())
        lines = cached.read_text().splitlines()[:PUZZLES_PER_FILE]
        digits += [line.split()[1] for line in lines]
    return digits


def to_cells(digits: str) -> list[list[int]]:
    return [[int(digits[r * GRID_SIZE + c]) for c in range(GRID_SIZE)] for r in range(GRID_SIZE)]


def solve_all(puzzles: list[list[list[int]]]) -> list[tuple[list[list[int]], list[list[int]]]]:
    """Pair each puzzle with its solution. Dancing Links is used because it
    is by far the fastest solver here, and this runs tens of thousands of
    times. Cached, since it costs minutes and the answers never change."""
    cache = CACHE_DIR / f"solutions_{len(puzzles)}.json"
    if cache.exists():
        print(f"reusing cached solutions ({cache.name})")
        return [(p, s) for p, s in json.loads(cache.read_text())]

    solver = DancingLinksSolver()
    pairs = []
    start = time.time()
    for i, cells in enumerate(puzzles):
        result = solver.solve(Board(cells=cells))
        if result.solved:
            pairs.append((cells, result.solved_board.cells))
        if (i + 1) % 5000 == 0:
            print(f"  solved {i + 1}/{len(puzzles)} ({time.time() - start:.0f}s)")
    cache.write_text(json.dumps(pairs))
    return pairs


def build_examples(
    pairs: list[tuple[list[list[int]], list[list[int]]]], rng: random.Random
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    inputs, targets, masks = [], [], []
    for puzzle, solution in pairs:
        empty = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if puzzle[r][c] == 0]
        for _ in range(BOARDS_PER_PUZZLE):
            # Reveal a random share of the solution, so the model sees boards
            # from "as given" through to nearly finished.
            reveal_count = int(rng.random() * len(empty))
            revealed = set(rng.sample(empty, reveal_count))
            board = [
                [solution[r][c] if (r, c) in revealed else puzzle[r][c] for c in range(GRID_SIZE)]
                for r in range(GRID_SIZE)
            ]
            inputs.append(encode_board(board))
            targets.append(torch.tensor(solution, dtype=torch.long) - 1)
            masks.append(torch.tensor([[cell == 0 for cell in row] for row in board]))
    return torch.stack(inputs), torch.stack(targets), torch.stack(masks)


def masked_cross_entropy(
    logits: torch.Tensor, targets: torch.Tensor, mask: torch.Tensor
) -> torch.Tensor:
    log_probs = F.log_softmax(logits, dim=1)
    nll = -log_probs.gather(1, targets.unsqueeze(1)).squeeze(1)
    return nll[mask].mean()


def masked_accuracy(logits: torch.Tensor, targets: torch.Tensor, mask: torch.Tensor) -> float:
    return (logits.argmax(dim=1) == targets)[mask].float().mean().item()


def solve_rate(model: torch.nn.Module, held_out: list[tuple[list[list[int]], list[list[int]]]]):
    """Runs the real inference loop the shipped solver uses: repeatedly place
    the most confident legal digit. Per-cell accuracy says little about
    whether a puzzle actually gets finished, which is the number that
    matters."""
    solved = 0
    filled_fractions = []
    for puzzle, solution in held_out:
        cells = [row[:] for row in puzzle]
        while any(0 in row for row in cells):
            best = most_confident_valid_placement(cells, predict(model, cells))
            if best is None:
                break
            _, r, c, value = best
            cells[r][c] = value
        if cells == solution:
            solved += 1
        filled = sum(1 for row in cells for v in row if v != 0)
        filled_fractions.append(filled / 81)
    return solved / len(held_out), sum(filled_fractions) / len(filled_fractions)


def main() -> None:
    torch.manual_seed(SEED)
    rng = random.Random(SEED)

    digits = fetch_puzzle_digits()
    rng.shuffle(digits)
    print(f"{len(digits)} puzzles, solving them for labels ...")
    pairs = solve_all([to_cells(d) for d in digits])

    held_out, train_pairs = pairs[:HELD_OUT_PUZZLES], pairs[HELD_OUT_PUZZLES:]
    print(f"{len(train_pairs)} training puzzles, {len(held_out)} held out")

    X, Y, M = build_examples(train_pairs, rng)
    print(f"{X.shape[0]} training boards")

    n_val = int(X.shape[0] * VAL_FRACTION)
    perm = torch.randperm(X.shape[0], generator=torch.Generator().manual_seed(SEED))
    val_idx, train_idx = perm[:n_val], perm[n_val:]
    X_train, Y_train, M_train = X[train_idx], Y[train_idx], M[train_idx]
    X_val, Y_val, M_val = X[val_idx], Y[val_idx], M[val_idx]

    model = SudokuCNN()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

    n_train = X_train.shape[0]
    for epoch in range(EPOCHS):
        model.train()
        epoch_perm = torch.randperm(n_train)
        total_loss = 0.0
        for start in range(0, n_train, BATCH_SIZE):
            batch = epoch_perm[start : start + BATCH_SIZE]
            logits = model(X_train[batch])
            loss = masked_cross_entropy(logits, Y_train[batch], M_train[batch])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * batch.numel()
        scheduler.step()

        model.eval()
        with torch.no_grad():
            val_acc = masked_accuracy(model(X_val), Y_val, M_val)
        avg_loss = total_loss / n_train
        print(
            f"epoch {epoch + 1}/{EPOCHS}: loss={avg_loss:.4f} val_cell_acc={val_acc:.3f}",
            flush=True,
        )

    rate, filled = solve_rate(model, held_out)
    print(f"held-out solve rate: {rate:.0%}  (avg board filled: {filled:.1%})")

    WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), WEIGHTS_PATH)
    print(f"saved weights to {WEIGHTS_PATH}")


if __name__ == "__main__":
    main()
