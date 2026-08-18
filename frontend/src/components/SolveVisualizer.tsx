import { applySteps } from "../playback/applySteps";
import type { BoardCells, SolveResult } from "../playback/types";
import { usePlayback } from "../playback/usePlayback";
import { Board } from "./Board";
import { PlaybackControls } from "./PlaybackControls";
import "./SolveVisualizer.css";

interface SolveVisualizerProps {
  initialCells: BoardCells;
  result: SolveResult;
}

/** Consumes any SolveResult, regardless of which algorithm produced it —
 * this component must not be forked per-algorithm. */
export function SolveVisualizer({ initialCells, result }: SolveVisualizerProps) {
  const { state, dispatch } = usePlayback(result.steps.length);
  const cells = applySteps(initialCells, result.steps, state.stepIndex);
  const lastStep = state.stepIndex > 0 ? result.steps[state.stepIndex - 1] : null;

  return (
    <section className="solve-visualizer">
      <Board cells={cells} givenCells={initialCells} activeCell={lastStep?.cell ?? null} />
      <PlaybackControls state={state} dispatch={dispatch} />
      <dl className="solve-stats">
        <div>
          <dt>Algorithm</dt>
          <dd>{result.stats.algorithm}</dd>
        </div>
        <div>
          <dt>Solved</dt>
          <dd>{result.solved ? "Yes" : "No"}</dd>
        </div>
        <div>
          <dt>Elapsed</dt>
          <dd>{(result.stats.elapsed_time * 1000).toFixed(2)} ms</dd>
        </div>
        <div>
          <dt>Total steps</dt>
          <dd>{result.stats.step_count}</dd>
        </div>
      </dl>
    </section>
  );
}
