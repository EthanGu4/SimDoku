from fastapi import APIRouter

from app.core import BENCHMARK_PUZZLES, BenchmarkPuzzle

router = APIRouter(prefix="/puzzles", tags=["puzzles"])


@router.get("")
def list_puzzles() -> list[BenchmarkPuzzle]:
    return BENCHMARK_PUZZLES
