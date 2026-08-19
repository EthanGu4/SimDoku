from app.api.board import router as board_router
from app.api.puzzles import router as puzzles_router
from app.api.race import router as race_router
from app.api.solve import router as solve_router

__all__ = ["board_router", "puzzles_router", "race_router", "solve_router"]
