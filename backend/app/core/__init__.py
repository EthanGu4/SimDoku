from app.core.history import BenchmarkRun, get_runs, record_run
from app.core.puzzles import BENCHMARK_PUZZLES, BenchmarkPuzzle, get_puzzle
from app.core.rules import is_complete, is_valid_board, is_valid_placement
from app.core.schemas import Board, SolveResult, SolveStats, SolveStep

__all__ = [
    "BENCHMARK_PUZZLES",
    "Board",
    "BenchmarkPuzzle",
    "BenchmarkRun",
    "SolveResult",
    "SolveStats",
    "SolveStep",
    "get_puzzle",
    "get_runs",
    "is_complete",
    "is_valid_board",
    "is_valid_placement",
    "record_run",
]
