from fastapi import APIRouter, HTTPException

from app.core import Board, SolveResult, is_valid_board
from app.solvers import get_solver, list_solvers

router = APIRouter(prefix="/solve", tags=["solve"])


@router.get("/algorithms")
def get_algorithms() -> list[str]:
    return list_solvers()


@router.post("/{algorithm}")
def solve(algorithm: str, board: Board) -> SolveResult:
    solver = get_solver(algorithm)
    if solver is None:
        raise HTTPException(status_code=404, detail=f"unknown algorithm: {algorithm}")

    if not is_valid_board(board.cells):
        raise HTTPException(status_code=400, detail="board violates Sudoku rules")

    return solver.solve(board)
