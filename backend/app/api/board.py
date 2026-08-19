from fastapi import APIRouter, HTTPException, UploadFile

from app.core import Board
from app.ml.board_detection import BoardDetectionError, detect_board

router = APIRouter(prefix="/board", tags=["board"])


@router.post("/detect")
async def detect(image: UploadFile) -> Board:
    image_bytes = await image.read()
    try:
        return detect_board(image_bytes)
    except BoardDetectionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
