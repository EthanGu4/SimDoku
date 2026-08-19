"""Generates synthetic (partial board -> solved board) puzzles via
randomized backtracking, trains SudokuCNN on them, and writes weights to
app/ml/weights/neural_solver.pt.

A dev-time tool, not run at request time. Re-run whenever the model
architecture in app/ml/neural_solver.py changes.

Usage (from backend/, with the venv active):
    python -m scripts.train_neural_solver
"""

import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.rules import is_valid_placement  # noqa: E402
from app.ml.sudoku_cnn import WEIGHTS_PATH, SudokuCNN, encode_board  # noqa: E402

GRID_SIZE = 9
NUM_BOARDS = 6000
# Givens kept, spanning our HARD..easy range plus a heavy skew toward
# near-complete boards — the iterative solver spends most of its life in
# that "almost done, deduce the last few cells" regime, so it needs to be
# very good there specifically, not just at the initial 21-55 given range.
MASK_LEVELS = [21, 24, 28, 32, 38, 46, 55, 62, 68, 72, 75, 77, 79, 80]
EPOCHS = 30
BATCH_SIZE = 256
LEARNING_RATE = 1e-3
VAL_FRACTION = 0.08
SEED = 0


def generate_solved_board(rng: random.Random) -> list[list[int]]:
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


def make_example(
    solved: list[list[int]], rng: random.Random, keep: int
) -> tuple[list[list[int]], np.ndarray, np.ndarray]:
    """A partial board with `keep` cells filled in, plus the full solution
    (as 0-8 class indices) and a mask of which cells were left empty."""
    positions = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)]
    rng.shuffle(positions)
    keep_set = set(positions[:keep])

    partial = [
        [solved[r][c] if (r, c) in keep_set else 0 for c in range(GRID_SIZE)]
        for r in range(GRID_SIZE)
    ]
    target = np.array(solved, dtype=np.int64) - 1
    mask = np.array([[(r, c) not in keep_set for c in range(GRID_SIZE)] for r in range(GRID_SIZE)])
    return partial, target, mask


def masked_cross_entropy(
    logits: torch.Tensor, targets: torch.Tensor, mask: torch.Tensor
) -> torch.Tensor:
    log_probs = F.log_softmax(logits, dim=1)
    nll = -log_probs.gather(1, targets.unsqueeze(1)).squeeze(1)
    return nll[mask].mean()


def masked_accuracy(logits: torch.Tensor, targets: torch.Tensor, mask: torch.Tensor) -> float:
    predicted = logits.argmax(dim=1)
    correct = (predicted == targets)[mask]
    return correct.float().mean().item()


def build_dataset() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    rng = random.Random(SEED)
    inputs, targets, masks = [], [], []

    print(f"generating {NUM_BOARDS} solved boards x {len(MASK_LEVELS)} mask levels...")
    start = time.time()
    for i in range(NUM_BOARDS):
        solved = generate_solved_board(rng)
        for keep in MASK_LEVELS:
            partial, target, mask = make_example(solved, rng, keep)
            inputs.append(encode_board(partial))
            targets.append(torch.from_numpy(target))
            masks.append(torch.from_numpy(mask))
        if (i + 1) % 500 == 0:
            print(f"  {i + 1}/{NUM_BOARDS} boards ({time.time() - start:.1f}s)")

    return torch.stack(inputs), torch.stack(targets).long(), torch.stack(masks)


def main() -> None:
    torch.manual_seed(SEED)
    X, Y, M = build_dataset()

    n = X.shape[0]
    n_val = int(n * VAL_FRACTION)
    perm = torch.randperm(n, generator=torch.Generator().manual_seed(SEED))
    val_idx, train_idx = perm[:n_val], perm[n_val:]
    X_train, Y_train, M_train = X[train_idx], Y[train_idx], M[train_idx]
    X_val, Y_val, M_val = X[val_idx], Y[val_idx], M[val_idx]
    print(f"train: {X_train.shape[0]} examples, val: {X_val.shape[0]} examples")

    model = SudokuCNN()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

    n_train = X_train.shape[0]
    for epoch in range(EPOCHS):
        model.train()
        epoch_perm = torch.randperm(n_train)
        total_loss = 0.0
        for start_idx in range(0, n_train, BATCH_SIZE):
            batch_idx = epoch_perm[start_idx : start_idx + BATCH_SIZE]
            xb, yb, mb = X_train[batch_idx], Y_train[batch_idx], M_train[batch_idx]

            logits = model(xb)
            loss = masked_cross_entropy(logits, yb, mb)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * xb.size(0)
        scheduler.step()

        model.eval()
        with torch.no_grad():
            val_logits = model(X_val)
            val_acc = masked_accuracy(val_logits, Y_val, M_val)
        avg_loss = total_loss / n_train
        print(f"epoch {epoch + 1}/{EPOCHS}: loss={avg_loss:.4f} val_masked_acc={val_acc:.3f}")

    WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), WEIGHTS_PATH)
    print(f"saved weights to {WEIGHTS_PATH}")


if __name__ == "__main__":
    main()
