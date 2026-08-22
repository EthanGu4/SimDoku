from fastapi import APIRouter

from app.core.puzzle_bank import BankPuzzle, Difficulty, get_random_puzzle

router = APIRouter(prefix="/puzzles", tags=["puzzles"])


@router.get("/random")
def random_puzzle(difficulty: Difficulty) -> BankPuzzle:
    """One puzzle from the graded bank, for the comparison view to run every
    algorithm against."""
    return get_random_puzzle(difficulty)
