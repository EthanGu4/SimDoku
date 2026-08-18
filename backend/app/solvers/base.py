"""The interface every solving algorithm implements, plus the registry it
self-registers into.

Adding a new algorithm = one new module here (or in app/ml/) that defines a
SolverStrategy and calls `register(...)` at import time, plus a corresponding
import line in this package's `__init__.py`. Nothing else should need to
change — not the API route, not the frontend, not the visualizer.
"""

from typing import Protocol

from app.core import Board, SolveResult


class SolverStrategy(Protocol):
    name: str

    def solve(self, board: Board) -> SolveResult: ...


_REGISTRY: dict[str, SolverStrategy] = {}


def register(solver: SolverStrategy) -> SolverStrategy:
    _REGISTRY[solver.name] = solver
    return solver


def get_solver(name: str) -> SolverStrategy | None:
    return _REGISTRY.get(name)


def list_solvers() -> list[str]:
    return sorted(_REGISTRY)
