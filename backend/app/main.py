from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import board_router, puzzles_router, race_router, solve_router

app = FastAPI(title="SimDoku API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(solve_router)
app.include_router(puzzles_router)
app.include_router(race_router)
app.include_router(board_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
