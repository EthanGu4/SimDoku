# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

SimDoku is a multi-layered Sudoku simulation: it visualizes multiple different Sudoku-solving algorithms running step-by-step in a UI, adds them one at a time, and eventually layers in ML (photo-based board detection, unconventional ML solving methods, and an ML model that predicts the fastest algorithm for a given puzzle and races it live against single-algorithm solves).

Stack: **Vite + React (TypeScript)** frontend, **FastAPI (Python)** backend, single monorepo.

```
/frontend        Vite + React + TypeScript
/backend
  /app
    /solvers      # one file per algorithm, implements SolverStrategy
    /ml           # ML modules (board detection, ML solvers, algorithm picker)
    /api          # FastAPI routers
    /core         # Board / SolveStep / SolveResult Pydantic schemas
  /tests
```

## Core architecture — read this before adding a solving algorithm

Every solving algorithm (classical or ML) implements the same `SolverStrategy` interface and registers itself by name in a registry:

```python
solve(board: Board) -> SolveResult
```

`SolveResult` = the solved board + an ordered list of `SolveStep` diffs (`{action, cell, value, candidates_removed, reasoning?}`) + `stats` (server-measured elapsed compute time, step count, puzzle metadata).

**Adding a new algorithm should only ever mean: one new module under `backend/app/solvers/` (or `backend/app/ml/`) + one registry entry.** It must never require touching the API contract, the frontend, or the visualizer. If a change seems to require that, the abstraction is being violated — stop and reconsider rather than special-casing the new algorithm.

The `SolveStep` schema must tolerate degenerate traces (e.g., an ML solver that jumps straight from empty to solved) — algorithms that can't produce a meaningful step-by-step trace are still expected to reuse the same visualizer.

## Deliberate design decision: eager-compute, not streaming

The backend solves a puzzle synchronously and returns the *entire* step trace as one JSON response, plus a server-measured `elapsed_time` that is independent of animation speed. The frontend owns all playback (play/pause/step/scrub/speed) client-side by indexing into the step array — there is no SSE/websocket involved.

This is intentional: Sudoku solves are cheap (sub-second to low seconds even for worst-case brute force), so streaming would add complexity without benefit, and it cleanly separates "real algorithm performance" (used for benchmarking/the ML picker) from "animation speed" (a cosmetic UI slider). Do not introduce streaming/websockets for the general solve flow. If a specific future algorithm (e.g. an ML solver with real training/inference latency) is genuinely long-running, give *that one endpoint* a polling or websocket variant — don't rearchitect the whole flow around it.

## Frontend visualizer

One generic `<SolveVisualizer>` + `<Board>` + playback-controls component set consumes any `SolveResult`, regardless of which algorithm produced it. It was built once in Phase 1 and should not be rewritten or forked per-algorithm — new algorithms are a backend-only change.

Frontend TS types for the API contract are generated from the backend's OpenAPI schema (e.g. via `openapi-typescript`) rather than hand-duplicated, to avoid drift.

## Testing

Every new solver module (`backend/app/solvers/*.py` or `backend/app/ml/*.py`) must ship a pytest correctness battery: a fixed set of puzzles with known solutions, asserting the algorithm solves them correctly and that replaying its `SolveStep` trace reproduces the same solved board.

Frontend testing is limited to the visualizer/playback reducer logic (Vitest + React Testing Library) — not full e2e coverage.

CI (GitHub Actions) runs lint + test on push to main. No deploy pipeline, environment matrix, or coverage gate until the project reaches the polish/deploy phase.

## Roadmap / phase status

Tracks actual implementation state — update as phases land. This section is the source of truth for "what exists right now," not the aspirational description above.

- [x] **Phase 0 — Foundations.** Monorepo skeleton, tooling, CI.
- [x] **Phase 1 — Core visualization engine + first algorithm.** `Board`/`SolveStep`/`SolveResult` schemas, `SolverStrategy` registry, backtracking solver, `POST /solve/{algorithm}`, generic `<SolveVisualizer>`.
- [x] **Phase 2 — Algorithm plug-in expansion.** 2–4 more classical solvers (e.g. constraint propagation, Dancing Links, simulated annealing), one at a time.
- [x] **Phase 3 — Benchmark harness & "race mode".** Fixed puzzle dataset, timing/feature persistence, side-by-side multi-algorithm UI.
- [x] **Phase 4 — ML: photo board detection.** Image upload → CV pipeline → board JSON → existing solve flow.
- [x] **Phase 5 — ML: unconventional solving methods.** ML solver(s) behind the standard `SolverStrategy` interface.
- [ ] **Phase 6 — ML: algorithm picker / meta-solver.** Trained on Phase 3's benchmark data; a pseudo-solver that delegates to a registered algorithm.
- [ ] **Phase 7 — Polish/deploy (stretch).** Puzzle generator, run history, deployment, demo material.

Algorithms are always added one at a time, each self-contained.
