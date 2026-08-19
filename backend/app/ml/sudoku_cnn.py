"""The CNN architecture and board encoding shared by NeuralSolver (inference)
and scripts/train_neural_solver.py (training). Kept import-side-effect-free
— unlike neural_solver.py, importing this never touches the solver registry
or requires trained weights to already exist on disk."""

from pathlib import Path

import torch
from torch import nn

from app.core.schemas import GRID_SIZE

WEIGHTS_PATH = Path(__file__).parent / "weights" / "neural_solver.pt"
CHANNELS = 64
DEPTH = 6


class SudokuCNN(nn.Module):
    """Input: (batch, 9, 9, 9) one-hot digit-presence per cell.
    Output: (batch, 9, 9, 9) logits, dim 1 indexing digit-1 (0-8)."""

    def __init__(self, channels: int = CHANNELS, depth: int = DEPTH) -> None:
        super().__init__()
        layers: list[nn.Module] = [
            nn.Conv2d(GRID_SIZE, channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(channels),
            nn.ReLU(inplace=True),
        ]
        for _ in range(depth - 1):
            layers += [
                nn.Conv2d(channels, channels, kernel_size=3, padding=1),
                nn.BatchNorm2d(channels),
                nn.ReLU(inplace=True),
            ]
        self.backbone = nn.Sequential(*layers)
        self.head = nn.Conv2d(channels, GRID_SIZE, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.backbone(x))


def encode_board(cells: list[list[int]]) -> torch.Tensor:
    """One-hot encode a board as (9, 9, 9) = (digit_channel, row, col)."""
    x = torch.zeros(GRID_SIZE, GRID_SIZE, GRID_SIZE)
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            value = cells[row][col]
            if value != 0:
                x[value - 1, row, col] = 1.0
    return x
