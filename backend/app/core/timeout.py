"""Wall-clock-capped solving. Used by the dev-time scripts that curate the
puzzle bank and train the algorithm picker, so one pathologically slow
puzzle (simulated annealing on a sparse board can take seconds; plain
backtracking occasionally takes minutes) can never stall a whole run.

Python can't forcibly kill a thread, so a solve that blows the cap just
gets abandoned as an orphaned daemon thread; the caller moves on without
waiting for it. Safe because every solver copies its input at the top of
solve() and only ever mutates that local copy."""

import threading

from app.core.schemas import Board, SolveResult
from app.solvers.base import SolverStrategy


def solve_with_timeout(
    solver: SolverStrategy, board: Board, timeout_seconds: float
) -> SolveResult | None:
    result_holder: dict[str, SolveResult] = {}

    def run() -> None:
        result_holder["result"] = solver.solve(board)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)
    if thread.is_alive():
        return None
    return result_holder.get("result")
