import { useEffect } from "react";
import { applySteps } from "../playback/applySteps";
import { describeStep } from "../playback/describeStep";
import type { BoardCells, SolveResult } from "../playback/types";
import { usePlayback } from "../playback/usePlayback";
import { Board } from "./Board";
import { PlaybackControls } from "./PlaybackControls";
import "./SolveVisualizer.css";

interface SolveVisualizerProps {
  initialCells: BoardCells;
  result: SolveResult;
  /** Starts playback immediately instead of waiting for the user to press
   * Play — used by race mode so every algorithm's board starts on the same
   * frame. Defaults to off so the single-solve view stays manual. */
  autoPlay?: boolean;
}

/** Consumes any SolveResult, regardless of which algorithm produced it —
 * this component must not be forked per-algorithm. */
export function SolveVisualizer({ initialCells, result, autoPlay }: SolveVisualizerProps) {
  const { state, dispatch } = usePlayback(result.steps.length);
  const cells = applySteps(initialCells, result.steps, state.stepIndex);
  const lastStep = state.stepIndex > 0 ? result.steps[state.stepIndex - 1] : null;

  useEffect(() => {
    if (!autoPlay) return;
    // Explicitly reset before playing rather than relying on usePlayback's
    // own totalSteps-keyed reset — two different results can coincidentally
    // have the same step count, which would otherwise skip the reset and
    // resume mid-way through instead of starting from the top.
    dispatch({ type: "reset" });
    dispatch({ type: "play" });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [result, autoPlay]);

  return (
    <section className="solve-visualizer">
      <Board cells={cells} givenCells={initialCells} lastStep={lastStep} />
      <p className="step-narration">{describeStep(lastStep)}</p>
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
      </dl>
    </section>
  );
}
