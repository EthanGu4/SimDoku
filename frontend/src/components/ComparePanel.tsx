import { useMemo } from "react";
import { applySteps } from "../playback/applySteps";
import type { BoardCells, SolveResult } from "../playback/types";
import { AlgorithmIcon } from "./AlgorithmIcon";
import { Board } from "./Board";

interface ComparePanelProps {
  algorithm: string;
  result: SolveResult;
  givenCells: BoardCells;
  /** Shared 0-1 position along the normalized timeline. */
  progress: number;
}

/** One algorithm's board in the side-by-side comparison.
 *
 * Maps the shared progress fraction onto this algorithm's own step count,
 * so every panel starts and finishes together no matter how many steps it
 * actually took. That difference in steps-per-tick is the whole point:
 * a solver that needs thousands of steps visibly churns while one that
 * needs fifty moves deliberately, on the identical puzzle. */
export function ComparePanel({ algorithm, result, givenCells, progress }: ComparePanelProps) {
  const totalSteps = result.steps.length;
  const stepIndex = Math.round(progress * totalSteps);

  const cells = useMemo(
    () => applySteps(givenCells, result.steps, stepIndex),
    [givenCells, result.steps, stepIndex],
  );
  const lastStep = stepIndex > 0 ? result.steps[stepIndex - 1] : null;

  return (
    <div className="compare-panel">
      <h3>
        <AlgorithmIcon algorithm={algorithm} size={15} />
        {algorithm.replace(/_/g, " ")}
      </h3>

      <Board cells={cells} givenCells={givenCells} lastStep={lastStep} />

      <div className="compare-stats">
        <span className="compare-steps">
          <strong>{stepIndex.toLocaleString()}</strong> / {totalSteps.toLocaleString()} steps
        </span>
        <span className={result.solved ? "compare-solved" : "compare-unsolved"}>
          {result.solved ? "Solved" : "Unsolved"}
        </span>
      </div>
    </div>
  );
}
