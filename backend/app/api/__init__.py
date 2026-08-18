from app.api.benchmark import router as benchmark_router
from app.api.puzzles import router as puzzles_router
from app.api.solve import router as solve_router

__all__ = ["benchmark_router", "puzzles_router", "solve_router"]
