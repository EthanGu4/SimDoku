import type { AlgorithmProgress } from "../playback/types";
import { Board } from "./Board";

interface RacePanelProps {
  algorithm: string;
  progress: AlgorithmProgress | undefined;
  puzzleCount: number;
}

function formatSeconds(seconds: number): string {
  return seconds < 1 ? `${Math.round(seconds * 1000)}ms` : `${seconds.toFixed(2)}s`;
}

/** One algorithm's lane in a live race: shows whatever puzzle it's
 * actually reached so far — not a synchronized reveal — so a fast
 * algorithm visibly pulls ahead of a slow one. Polled progress arrives in
 * bursts, not one puzzle at a time; this just always shows the latest
 * result it has. */
export function RacePanel({ algorithm, progress, puzzleCount }: RacePanelProps) {
  const results = progress?.results ?? [];
  const current = results[results.length - 1];
  const solvedCount = results.filter((r) => r.solved).length;
  const elapsedTotal = results.reduce((sum, r) => sum + r.elapsed_time, 0);
  const done = progress?.done ?? false;
  const dnfCount = done ? puzzleCount - results.length : 0;

  return (
    <div className="race-panel">
      <h3>{algorithm.replace(/_/g, " ")}</h3>

      <div className="race-progress-track">
        <div
          className="race-progress-fill"
          style={{ width: `${puzzleCount > 0 ? (results.length / puzzleCount) * 100 : 0}%` }}
        />
      </div>

      <div className="race-board-wrap">
        {current ? (
          <>
            <div key={results.length} className="race-board-pop">
              <Board cells={current.solved_board.cells} givenCells={current.given_board.cells} />
            </div>
            {!current.solved && (
              <span className="dnf-badge" title="Didn't finish this puzzle">
                DNF
              </span>
            )}
          </>
        ) : (
          <div className="race-board-placeholder" />
        )}
      </div>

      <div className="race-stats">
        <span>
          {done ? "Solved" : "So far"} {solvedCount}/{results.length || puzzleCount}
          {dnfCount > 0 && ` (+${dnfCount} cut off)`}
        </span>
        <span>{formatSeconds(elapsedTotal)}</span>
      </div>
    </div>
  );
}
