import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import board_router, puzzles_router, solve_router

# Where the Docker image drops the built frontend. Absent in local dev, where
# Vite serves it instead and proxies the API prefixes here.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="SimDoku API")

# Only needed when the frontend is served from a different origin than this
# API. The bundled deployment serves both from one origin, so this defaults
# to the Vite dev server alone.
cors_origins = os.getenv("SIMDOKU_CORS_ORIGINS", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins.split(",") if origin.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(solve_router)
app.include_router(puzzles_router)
app.include_router(board_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Mounted last so every API route above wins the match first. `html=True`
# serves index.html for unknown paths, which is what a single-page app needs.
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
