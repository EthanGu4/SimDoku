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

CI (GitHub Actions) runs lint + test on push to main. No environment matrix or coverage gate; deployment is a `Dockerfile` built by hand or by the host, not a pipeline.

## Roadmap / phase status

Tracks actual implementation state — update as phases land. This section is the source of truth for "what exists right now," not the aspirational description above.

- [x] **Phase 0 — Foundations.** Monorepo skeleton, tooling, CI.
- [x] **Phase 1 — Core visualization engine + first algorithm.** `Board`/`SolveStep`/`SolveResult` schemas, `SolverStrategy` registry, backtracking solver, `POST /solve/{algorithm}`, generic `<SolveVisualizer>`.
- [x] **Phase 2 — Algorithm plug-in expansion.** 2–4 more classical solvers (e.g. constraint propagation, Dancing Links, simulated annealing), one at a time. Later joined by two more, both added to give the comparison view a wider spread:
  - `x_wing_swordfish` (`app/solvers/fish_patterns.py`) layers the X-Wing and Swordfish candidate eliminations on top of constraint propagation. Its single-finding order deliberately mirrors `constraint_propagation` exactly, so the two produce identical traces on puzzles where no fish pattern fires and any difference is attributable to the eliminations alone (a test enforces this). The patterns fire on roughly 1 in 7 bank puzzles and cut total steps ~5%.
  - `genetic` (`app/solvers/genetic.py`) breeds a population of whole grids. It is included precisely because it is *bad* at Sudoku: measured across easy puzzles it essentially never finishes, stalling 2-6 conflicts short in a local optimum where no single mutation improves fitness. Larger populations and several times the generation budget were measured and do not rescue it, so the budget is deliberately small rather than slow-and-equally-doomed. Do not "fix" it by bolting on local search; that turns it into a memetic algorithm and loses the point, which is showing what a pure GA does here. Fitness is cached per organism because selection would otherwise rescore unchanged grids thousands of times per generation (that mistake cost ~4x runtime).
- [x] **Phase 3 — Benchmark harness, now the side-by-side comparison view.** Went through a batch "race mode" (all algorithms racing 100 puzzles, live-polled) before being replaced outright: with solvers ranging from sub-millisecond to multi-second, a race just showed the fast ones lapping the slow ones and read as broken rather than informative. What replaced it: `<ComparePage>` runs *every* algorithm against one puzzle from the graded bank and plays their real step traces side by side. A single shared control drives a normalized 0-100% timeline that each panel maps onto its own step count, so every board starts and finishes together and the visible difference is how hard each one had to work (on one hard puzzle: 134 steps for Dancing Links, 2,676 for backtracking, 17,042 for simulated annealing). Panels sort fewest-steps-first. The puzzle bank itself (`app/core/puzzle_bank.py`, `data/puzzle_bank.json`, `scripts/import_puzzle_bank.py`) is the surviving piece of the old race mode: 100 puzzles per difficulty from `grantm/sudoku-exchange-puzzle-bank` (public domain), committed as a static fixture and served one at a time by `GET /puzzles/random`. No streaming, no persistence, no run history.
- [x] **Phase 4 — ML: photo board detection.** Image upload → CV pipeline → board JSON → existing solve flow.
- [x] **Phase 5 — ML: unconventional solving methods.** `neural_net` (`app/ml/neural_solver.py`, architecture in `sudoku_cnn.py`) is a CNN that places its most confident legal digit each round. It went from solving 0% of puzzles to 41% overall (71% easy, 37% medium, 14% hard on 300 unseen puzzles) via two fixes, both found by measuring rather than guessing. First, the original training data was mostly *unlabelable*: blanking random cells from a solved grid yields puzzles with many valid completions (0% were uniquely solvable at 21 givens), so the net was penalized for answering correctly but differently. Training now uses real puzzles and reveals correct cells to build mid-solve boards, which keeps every label unique. Second, stacked 3x3 convolutions are the wrong inductive bias: Sudoku's constraints run along whole rows and columns, which a 3x3 window never sees. Each block now has parallel 1x9, 9x1 and 3x3 branches, worth ~10x on solve rate by itself. Note that per-cell accuracy is a misleading proxy (84% accuracy still fails most puzzles, since finishing needs a long chain of correct placements), and that a 60-puzzle eval was too noisy to rank checkpoints and ranked them backwards; use `scripts/eval_neural_solver.py`, which tests on puzzles past the training cutoff.
- [x] **Phase 6 — ML: algorithm picker / meta-solver.** `algorithm_picker` is a pseudo-solver (`app/ml/algorithm_picker.py`) that extracts a few structural features (given count, min/avg/max candidates per empty cell — `app/ml/algorithm_features.py`), uses a small decision tree to predict which of the three *complete* solvers (backtracking, constraint propagation, dancing links) will be fastest, and delegates to it — simulated annealing and the neural net are deliberately excluded as candidates since they can fail to solve at all. Trained on-demand from the puzzle bank (`scripts/train_algorithm_picker.py`), not from persisted history. Notable finding from real timing data: dancing links' O(1) backtrack makes it fastest on nearly every real puzzle tried, so the training set needed synthetic near-complete puzzles added just to surface the (real, but narrow) region where constraint propagation wins instead.
- [x] **Phase 7 — Deploy + demo material.** Single-image `Dockerfile`: the frontend is built and served by the backend, so there is one process, one port, and no CORS to configure. The frontend calls the API with same-origin relative URLs, with a Vite dev proxy (`vite.config.ts`) making that work in local dev too. Torch is installed from the CPU wheel index in both the image and CI, since plain `pip install torch` on Linux pulls the multi-GB CUDA build for a 9x9 board that never touches a GPU. README rewritten as demo material with real screenshots in `docs/`. The puzzle generator and run history originally sketched for this phase were dropped as unnecessary.

Algorithms are always added one at a time, each self-contained.
