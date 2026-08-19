"""Race mode's concurrent runner: starts every algorithm's 100-puzzle batch
as its own subprocess and lets the caller poll for progress as each one
works through its puzzles at its own true pace. This is what makes a race
genuine — a fast algorithm visibly pulls ahead of a slow one — instead of
computing everything up front and faking a synchronized reveal.

A thread-based per-puzzle timeout was tried first and rejected: an
abandoned thread keeps running (Python can't forcibly kill a thread), so
on a puzzle set where most attempts time out (simulated annealing on
sparse puzzles routinely does), zombie threads pile up and fight for the
GIL — everything gets slower, including unrelated work in the same
process. A subprocess can be *actually* terminated, which fully reclaims
its CPU; nothing leaks.

This deliberately bends the app's usual "eager-compute, no streaming"
rule — CLAUDE.md carves out exactly this exception for a genuinely
long-running endpoint. It's polling, not a websocket: simpler, and the
~300ms cadence the frontend uses is more than fine for a visual race."""

import multiprocessing as mp
import queue
import threading
import time
import uuid
from dataclasses import dataclass, field

from app.core.race_puzzles import RacePuzzle
from app.core.schemas import Board

PER_ALGORITHM_TIMEOUT_SECONDS = 30.0
RACE_TTL_SECONDS = 600.0  # finished races are swept up so memory doesn't grow forever


@dataclass
class RaceAttempt:
    puzzle_index: int
    solved: bool
    elapsed_time: float
    solved_cells: list[list[int]]


@dataclass
class AlgorithmRace:
    process: "mp.process.BaseProcess"
    result_queue: "mp.Queue[RaceAttempt]"
    results: list[RaceAttempt | None]
    done: bool = False


@dataclass
class Race:
    puzzles: list[RacePuzzle]
    created_at: float = field(default_factory=time.monotonic)
    algorithms: dict[str, AlgorithmRace] = field(default_factory=dict)


_races: dict[str, Race] = {}
_lock = threading.Lock()


def _worker(
    algorithm: str, puzzles: list[list[list[int]]], result_queue: "mp.Queue[RaceAttempt]"
) -> None:
    # Imported here, not at module scope: this only ever runs inside the
    # spawned subprocess, and importing the solver registry loads every
    # solver — including the neural net's torch model — so there's no
    # reason to pay that cost in the parent server process too.
    from app.solvers import get_solver

    solver = get_solver(algorithm)
    if solver is None:
        return

    for index, cells in enumerate(puzzles):
        result = solver.solve(Board(cells=cells))
        result_queue.put(
            RaceAttempt(
                puzzle_index=index,
                solved=result.solved,
                elapsed_time=result.stats.elapsed_time,
                solved_cells=result.solved_board.cells,
            )
        )


def start_race(algorithms: list[str], puzzles: list[RacePuzzle]) -> str:
    _sweep_stale_races()

    ctx = mp.get_context("spawn")
    cells = [p.board.cells for p in puzzles]
    race = Race(puzzles=puzzles)

    for algorithm in algorithms:
        result_queue: mp.Queue[RaceAttempt] = ctx.Queue()
        process = ctx.Process(target=_worker, args=(algorithm, cells, result_queue), daemon=True)
        process.start()
        race.algorithms[algorithm] = AlgorithmRace(
            process=process, result_queue=result_queue, results=[None] * len(puzzles)
        )

    race_id = uuid.uuid4().hex
    with _lock:
        _races[race_id] = race
    for algorithm in algorithms:
        threading.Timer(PER_ALGORITHM_TIMEOUT_SECONDS, _kill, args=(race_id, algorithm)).start()

    return race_id


def get_race(race_id: str) -> Race | None:
    with _lock:
        race = _races.get(race_id)
        if race is None:
            return None
        for algo_race in race.algorithms.values():
            _drain(algo_race)
        return race


def _drain(algo_race: AlgorithmRace) -> None:
    if algo_race.done:
        return
    while True:
        try:
            attempt = algo_race.result_queue.get_nowait()
        except queue.Empty:
            break
        algo_race.results[attempt.puzzle_index] = attempt
    if all(r is not None for r in algo_race.results):
        algo_race.done = True


def _kill(race_id: str, algorithm: str) -> None:
    """Runs on a timer thread once PER_ALGORITHM_TIMEOUT_SECONDS elapses,
    regardless of whether anyone is still polling — a struggling algorithm
    gets cut off even if the frontend gave up watching."""
    with _lock:
        race = _races.get(race_id)
        if race is None:
            return
        algo_race = race.algorithms.get(algorithm)
        if algo_race is None or algo_race.done:
            return
        algo_race.process.terminate()
        algo_race.done = True


def _sweep_stale_races() -> None:
    now = time.monotonic()
    with _lock:
        stale_ids = [
            rid for rid, race in _races.items() if now - race.created_at > RACE_TTL_SECONDS
        ]
        for rid in stale_ids:
            for algo_race in _races[rid].algorithms.values():
                if algo_race.process.is_alive():
                    algo_race.process.terminate()
            del _races[rid]
