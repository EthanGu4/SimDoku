import type { BoardCells, SolveStep } from "./types";

/** The board state after replaying the first `count` steps onto `initialCells`.
 * Mirrors backend/tests/test_backtracking.py's apply_steps helper — the two
 * must agree, since this is how the frontend proves it's faithfully
 * replaying the server's trace rather than re-deriving its own board state. */
export function applySteps(
  initialCells: BoardCells,
  steps: SolveStep[],
  count: number,
): BoardCells {
  const cells = initialCells.map((row) => [...row]);
  for (let i = 0; i < count && i < steps.length; i++) {
    const step = steps[i];
    const [row, col] = step.cell;
    cells[row][col] = step.action === "place" ? (step.value ?? 0) : 0;
  }
  return cells;
}
