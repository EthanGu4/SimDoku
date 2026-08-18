from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core import BenchmarkRun, SolveResult, get_puzzle, get_runs, record_run
from app.solvers import get_solver

router = APIRouter(prefix="/benchmark", tags=["benchmark"])


class BenchmarkRequest(BaseModel):
    puzzle_id: str


@router.post("/{algorithm}")
def run_benchmark(algorithm: str, request: BenchmarkRequest) -> SolveResult:
    solver = get_solver(algorithm)
    if solver is None:
        raise HTTPException(status_code=404, detail=f"unknown algorithm: {algorithm}")

    puzzle = get_puzzle(request.puzzle_id)
    if puzzle is None:
        raise HTTPException(status_code=404, detail=f"unknown puzzle: {request.puzzle_id}")

    result = solver.solve(puzzle.board)
    record_run(request.puzzle_id, result)
    return result


@router.get("/history")
def benchmark_history(puzzle_id: str | None = None) -> list[BenchmarkRun]:
    return get_runs(puzzle_id)
