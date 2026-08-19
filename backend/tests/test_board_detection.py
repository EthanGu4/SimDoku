"""Correctness battery for the photo -> Board pipeline.

Real photos aren't available in CI, so these tests render a puzzle to a
synthetic "photo" (a puzzle grid inset in a white page, like a phone photo of
a printed puzzle) and assert the pipeline reads it back correctly. Requires
the `tesseract` binary on PATH — skipped automatically if it isn't installed.
"""

import io
import shutil

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont

from app.core.puzzles import EASY_CELLS, MEDIUM_CELLS
from app.main import app
from app.ml.board_detection import BoardDetectionError, detect_board

pytestmark = pytest.mark.skipif(
    shutil.which("tesseract") is None, reason="tesseract binary not installed"
)

client = TestClient(app)

PAGE_SIZE = 1000
GRID_MARGIN = 50
GRID_SIZE = PAGE_SIZE - 2 * GRID_MARGIN
CELL_SIZE = GRID_SIZE // 9


def render_puzzle_photo(cells: list[list[int]]) -> bytes:
    image = Image.new("L", (PAGE_SIZE, PAGE_SIZE), color=255)
    draw = ImageDraw.Draw(image)

    for i in range(10):
        offset = GRID_MARGIN + i * CELL_SIZE
        width = 4 if i % 3 == 0 else 1
        draw.line([(offset, GRID_MARGIN), (offset, GRID_MARGIN + GRID_SIZE)], fill=0, width=width)
        draw.line([(GRID_MARGIN, offset), (GRID_MARGIN + GRID_SIZE, offset)], fill=0, width=width)

    font = ImageFont.load_default(size=int(CELL_SIZE * 0.65))
    for row in range(9):
        for col in range(9):
            value = cells[row][col]
            if value == 0:
                continue
            cx = GRID_MARGIN + col * CELL_SIZE + CELL_SIZE / 2
            cy = GRID_MARGIN + row * CELL_SIZE + CELL_SIZE / 2
            draw.text((cx, cy), str(value), fill=0, font=font, anchor="mm")

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.mark.parametrize("cells", [EASY_CELLS, MEDIUM_CELLS])
def test_detect_board_reads_synthetic_photo(cells: list[list[int]]) -> None:
    photo_bytes = render_puzzle_photo(cells)
    board = detect_board(photo_bytes)
    assert board.cells == cells


def test_detect_board_rejects_unreadable_image() -> None:
    with pytest.raises(BoardDetectionError):
        detect_board(b"not an image")


def test_detect_endpoint_returns_board() -> None:
    photo_bytes = render_puzzle_photo(EASY_CELLS)
    response = client.post(
        "/board/detect", files={"image": ("puzzle.png", photo_bytes, "image/png")}
    )
    assert response.status_code == 200
    assert response.json()["cells"] == EASY_CELLS


def test_detect_endpoint_rejects_bad_image() -> None:
    response = client.post(
        "/board/detect", files={"image": ("bad.png", b"not an image", "image/png")}
    )
    assert response.status_code == 400
