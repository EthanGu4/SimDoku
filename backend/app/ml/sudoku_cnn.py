"""The CNN architecture and board encoding shared by NeuralSolver (inference)
and scripts/train_neural_solver.py (training). Kept import-side-effect-free
— unlike neural_solver.py, importing this never touches the solver registry
or requires trained weights to already exist on disk."""

from pathlib import Path

import torch
from torch import nn

from app.core.rules import is_valid_placement
from app.core.schemas import GRID_SIZE

WEIGHTS_PATH = Path(__file__).parent / "weights" / "neural_solver.pt"
CHANNELS = 64
DEPTH = 4


class ConstraintBlock(nn.Module):
    """One residual block whose receptive fields match Sudoku's constraints:
    a full row, a full column, and a 3x3 box, mixed back together by a 1x1
    convolution.

    A stack of plain 3x3 convolutions was tried first and plateaued. 3x3 is
    the right bias for images, where what matters is spatially local, but
    Sudoku's rules are "these nine cells are distinct" along lines that a
    3x3 window never sees whole. Giving each branch the shape of an actual
    constraint lets a single layer relate every cell in a unit, rather than
    making the network approximate that through many local steps.

    This shapes the architecture, not the answer: no Sudoku rule is encoded
    anywhere, and every branch is still learned from data."""

    def __init__(self, channels: int) -> None:
        super().__init__()
        self.row = nn.Conv2d(channels, channels, kernel_size=(1, GRID_SIZE), padding=(0, 4))
        self.col = nn.Conv2d(channels, channels, kernel_size=(GRID_SIZE, 1), padding=(4, 0))
        self.box = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
        self.mix = nn.Conv2d(channels * 3, channels, kernel_size=1)
        self.norm = nn.BatchNorm2d(channels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        merged = torch.cat([self.row(x), self.col(x), self.box(x)], dim=1)
        return torch.relu(self.norm(self.mix(merged)) + x)


class SudokuCNN(nn.Module):
    """Input: (batch, 9, 9, 9) one-hot digit-presence per cell.
    Output: (batch, 9, 9, 9) logits, dim 1 indexing digit-1 (0-8)."""

    def __init__(self, channels: int = CHANNELS, depth: int = DEPTH) -> None:
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(GRID_SIZE, channels, kernel_size=1),
            nn.BatchNorm2d(channels),
            nn.ReLU(inplace=True),
        )
        self.backbone = nn.Sequential(*[ConstraintBlock(channels) for _ in range(depth)])
        self.head = nn.Conv2d(channels, GRID_SIZE, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.backbone(self.stem(x)))


def encode_board(cells: list[list[int]]) -> torch.Tensor:
    """One-hot encode a board as (9, 9, 9) = (digit_channel, row, col)."""
    x = torch.zeros(GRID_SIZE, GRID_SIZE, GRID_SIZE)
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            value = cells[row][col]
            if value != 0:
                x[value - 1, row, col] = 1.0
    return x


def predict(model: nn.Module, cells: list[list[int]]) -> torch.Tensor:
    """Per-cell probability distribution over digits 1-9, shaped (9, 9, 9)."""
    model.eval()
    with torch.no_grad():
        logits = model(encode_board(cells).unsqueeze(0))[0]
        return torch.softmax(logits, dim=0)


def most_confident_valid_placement(
    cells: list[list[int]], probs: torch.Tensor
) -> tuple[float, int, int, int] | None:
    """The (confidence, row, col, value) the model is surest about among
    placements that don't break Sudoku's rules, or None when some empty cell
    has no legal digit left and the board is therefore a dead end.

    Shared with the training script so evaluation measures the exact
    inference procedure that ships, rather than a lookalike that could drift
    from it."""
    best: tuple[float, int, int, int] | None = None
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if cells[row][col] != 0:
                continue
            for digit in torch.argsort(probs[:, row, col], descending=True).tolist():
                value = digit + 1
                if is_valid_placement(cells, row, col, value):
                    confidence = probs[digit, row, col].item()
                    if best is None or confidence > best[0]:
                        best = (confidence, row, col, value)
                    break
    return best
