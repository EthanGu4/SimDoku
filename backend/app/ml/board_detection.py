"""Photo -> Board pipeline: locate the puzzle grid in a photo, warp it to a
square, and OCR each cell. Produces the same `Board` schema every solver
already consumes, so a detected board flows straight into the existing solve
endpoint with no new contract.
"""

from __future__ import annotations

import cv2
import numpy as np
import pytesseract

from app.core.schemas import Board

GRID_SIZE = 9
WARPED_SIZE = 900  # -> 100px per cell
CELL_SIZE = WARPED_SIZE // GRID_SIZE
CELL_MARGIN = 12  # px trimmed from each edge before OCR, to drop grid lines from the crop
EMPTY_CELL_INK_THRESHOLD = 0.02  # fraction of dark pixels below which a cell counts as empty

TESSERACT_CONFIG = "--psm 6 -c tessedit_char_whitelist=123456789"


class BoardDetectionError(ValueError):
    """Raised when a puzzle grid can't be located or read from an image."""


def detect_board(image_bytes: bytes) -> Board:
    image = _decode_image(image_bytes)
    corners = _find_grid_corners(image)
    warped = _warp_to_square(image, corners)
    cells = [[_read_cell(warped, row, col) for col in range(GRID_SIZE)] for row in range(GRID_SIZE)]
    return Board(cells=cells)


def _decode_image(image_bytes: bytes) -> np.ndarray:
    buffer = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise BoardDetectionError("couldn't decode image")
    return image


def _find_grid_corners(image: np.ndarray) -> np.ndarray:
    blurred = cv2.GaussianBlur(image, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise BoardDetectionError("no puzzle grid found in image")

    largest = max(contours, key=cv2.contourArea)
    perimeter = cv2.arcLength(largest, True)
    approx = cv2.approxPolyDP(largest, 0.02 * perimeter, True)
    if len(approx) != 4:
        raise BoardDetectionError("couldn't find a 4-cornered puzzle grid in image")

    return _order_corners(approx.reshape(4, 2).astype(np.float32))


def _order_corners(points: np.ndarray) -> np.ndarray:
    """Order 4 points as top-left, top-right, bottom-right, bottom-left."""
    total = points.sum(axis=1)
    diff = np.diff(points, axis=1).reshape(-1)
    return np.array(
        [
            points[np.argmin(total)],
            points[np.argmin(diff)],
            points[np.argmax(total)],
            points[np.argmax(diff)],
        ],
        dtype=np.float32,
    )


def _warp_to_square(image: np.ndarray, corners: np.ndarray) -> np.ndarray:
    destination = np.array(
        [[0, 0], [WARPED_SIZE - 1, 0], [WARPED_SIZE - 1, WARPED_SIZE - 1], [0, WARPED_SIZE - 1]],
        dtype=np.float32,
    )
    transform = cv2.getPerspectiveTransform(corners, destination)
    return cv2.warpPerspective(image, transform, (WARPED_SIZE, WARPED_SIZE))


def _read_cell(warped: np.ndarray, row: int, col: int) -> int:
    y0, y1 = row * CELL_SIZE + CELL_MARGIN, (row + 1) * CELL_SIZE - CELL_MARGIN
    x0, x1 = col * CELL_SIZE + CELL_MARGIN, (col + 1) * CELL_SIZE - CELL_MARGIN
    cell = warped[y0:y1, x0:x1]

    _, cell_thresh = cv2.threshold(cell, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    ink_fraction = float(np.count_nonzero(cell_thresh)) / cell_thresh.size
    if ink_fraction < EMPTY_CELL_INK_THRESHOLD:
        return 0

    text = pytesseract.image_to_string(cell, config=TESSERACT_CONFIG).strip()
    return int(text[0]) if text[:1].isdigit() and text[0] != "0" else 0
