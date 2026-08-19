"""Race mode: every algorithm races through the same 100-puzzle batch
concurrently, each at its own true pace. POST /race/start kicks all of them
off in parallel subprocesses and returns immediately; the frontend polls
GET /race/{race_id}/progress to watch them diverge in real time — a fast
algorithm visibly pulls ahead of a slow one — instead of waiting for the
whole batch and faking a synchronized reveal.

Deliberately excludes step traces from progress results. A batch of 100
runs (some algorithms producing tens of thousands of steps each) would
bloat every poll response for no benefit — race mode's visualization is a
decorative reveal per puzzle, not a step-by-step replay.

See app.core.race_runner for why each algorithm's batch is wall-clock
capped in a real subprocess rather than the app's usual synchronous,
non-streaming solve flow."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core import Board
from app.core.race_puzzles import Difficulty, get_race_puzzles
from app.core.race_runner import get_race, start_race
from app.solvers import list_solvers

router = APIRouter(prefix="/race", tags=["race"])


class StartRaceResponse(BaseModel):
    race_id: str
    algorithms: list[str]
    puzzle_count: int


class RaceRunResult(BaseModel):
    puzzle_id: str
    solved: bool
    elapsed_time: float
    given_board: Board
    solved_board: Board


class AlgorithmProgress(BaseModel):
    done: bool
    results: list[RaceRunResult]


class RaceProgress(BaseModel):
    algorithms: dict[str, AlgorithmProgress]


@router.post("/start")
def start(difficulty: Difficulty) -> StartRaceResponse:
    algorithms = list_solvers()
    puzzles = get_race_puzzles(difficulty)
    race_id = start_race(algorithms, puzzles)
    return StartRaceResponse(race_id=race_id, algorithms=algorithms, puzzle_count=len(puzzles))


@router.get("/{race_id}/progress")
def progress(race_id: str) -> RaceProgress:
    race = get_race(race_id)
    if race is None:
        raise HTTPException(status_code=404, detail=f"unknown race_id: {race_id}")

    algorithms: dict[str, AlgorithmProgress] = {}
    for algorithm, algo_race in race.algorithms.items():
        results: list[RaceRunResult] = []
        for puzzle, attempt in zip(race.puzzles, algo_race.results):
            if attempt is None:
                break  # keep results a dense, in-order prefix
            results.append(
                RaceRunResult(
                    puzzle_id=puzzle.id,
                    solved=attempt.solved,
                    elapsed_time=attempt.elapsed_time,
                    given_board=puzzle.board,
                    solved_board=Board(cells=attempt.solved_cells),
                )
            )
        algorithms[algorithm] = AlgorithmProgress(done=algo_race.done, results=results)

    return RaceProgress(algorithms=algorithms)
