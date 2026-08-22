import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { BankPuzzle, SolveResult } from "../playback/types";
import { usePlayback } from "../playback/usePlayback";
import { ComparePanel } from "./ComparePanel";
import { PlaybackControls } from "./PlaybackControls";
import "./ComparePage.css";

type Difficulty = "easy" | "medium" | "hard";

/** The shared timeline every algorithm is mapped onto: 100 ticks means the
 * scrubber reads directly as a percentage, and a speed of N ticks/second
 * plays the whole comparison in 100/N seconds. */
const TIMELINE_TICKS = 100;

export function ComparePage() {
  const [difficulty, setDifficulty] = useState<Difficulty>("easy");
  const [puzzle, setPuzzle] = useState<BankPuzzle | null>(null);
  const [results, setResults] = useState<Record<string, SolveResult>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { state, dispatch } = usePlayback(TIMELINE_TICKS);

  const runComparison = useCallback(async (forDifficulty: Difficulty) => {
    setError(null);
    setIsLoading(true);
    setResults({});
    setPuzzle(null);

    const [{ data: puzzleData }, { data: algorithmNames }] = await Promise.all([
      api.GET("/puzzles/random", { params: { query: { difficulty: forDifficulty } } }),
      api.GET("/solve/algorithms"),
    ]);

    if (!puzzleData || !algorithmNames) {
      setIsLoading(false);
      setError("Couldn't load a puzzle to compare. Try again.");
      return;
    }

    const responses = await Promise.all(
      algorithmNames.map((algorithm) =>
        api.POST("/solve/{algorithm}", {
          params: { path: { algorithm } },
          body: { cells: puzzleData.board.cells },
        }),
      ),
    );

    const next: Record<string, SolveResult> = {};
    responses.forEach((response, i) => {
      if (response.data) next[algorithmNames[i]] = response.data;
    });

    setIsLoading(false);

    if (Object.keys(next).length === 0) {
      setError("Couldn't run the algorithms on that puzzle. Try again.");
      return;
    }

    setPuzzle(puzzleData);
    setResults(next);
    dispatch({ type: "reset" });
    dispatch({ type: "play" });
  }, [dispatch]);

  useEffect(() => {
    runComparison("easy");
  }, [runComparison]);

  // Fewest steps first, so the most efficient solver leads the grid.
  const ordered = Object.keys(results).sort(
    (a, b) => results[a].steps.length - results[b].steps.length,
  );
  const progress = state.stepIndex / TIMELINE_TICKS;

  return (
    <section id="compare-page">
      <div className="controls-row">
        <select
          value={difficulty}
          onChange={(e) => {
            const next = e.target.value as Difficulty;
            setDifficulty(next);
            runComparison(next);
          }}
          disabled={isLoading}
        >
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>
        <span className="spacer" />
        <button
          type="button"
          className="primary"
          onClick={() => runComparison(difficulty)}
          disabled={isLoading}
        >
          {isLoading ? "Solving…" : "New puzzle"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {puzzle && ordered.length > 0 && (
        <>
          <div className="compare-timeline">
            <PlaybackControls
              state={state}
              dispatch={dispatch}
              progressLabel={`${state.stepIndex}% through every solve`}
              formatSpeed={(speed) => `${TIMELINE_TICKS / speed}s`}
            />
            <p className="compare-legend">
              Every algorithm solves the same puzzle and finishes together, so what differs is how
              much work each needs to get there. Green is a placement it kept, amber a digit
              rejected on the spot, red one it had to take back.
            </p>
          </div>

          <div className="compare-grid">
            {ordered.map((algorithm) => (
              <ComparePanel
                key={algorithm}
                algorithm={algorithm}
                result={results[algorithm]}
                givenCells={puzzle.board.cells}
                progress={progress}
              />
            ))}
          </div>
        </>
      )}
    </section>
  );
}
