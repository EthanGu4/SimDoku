import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { AlgorithmProgress } from "../playback/types";
import { RacePanel } from "./RacePanel";
import "./RaceMode.css";

type Difficulty = "easy" | "medium" | "hard";

const POLL_INTERVAL_MS = 300;

export function RaceMode() {
  const [difficulty, setDifficulty] = useState<Difficulty>("easy");
  const [algorithms, setAlgorithms] = useState<string[]>([]);
  const [puzzleCount, setPuzzleCount] = useState(0);
  const [progress, setProgress] = useState<Record<string, AlgorithmProgress> | null>(null);
  const [isRacing, setIsRacing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  async function handleRace() {
    setError(null);
    setProgress(null);
    if (pollRef.current) clearInterval(pollRef.current);

    const { data, error: apiError } = await api.POST("/race/start", {
      params: { query: { difficulty } },
    });

    if (apiError || !data) {
      setError("Couldn't start the race — try again.");
      return;
    }

    setAlgorithms(data.algorithms);
    setPuzzleCount(data.puzzle_count);
    setIsRacing(true);

    const raceId = data.race_id;
    pollRef.current = setInterval(async () => {
      const { data: progressData, error: progressError } = await api.GET(
        "/race/{race_id}/progress",
        { params: { path: { race_id: raceId } } },
      );

      if (progressError || !progressData) return;

      setProgress(progressData.algorithms);

      const allDone = Object.values(progressData.algorithms).every((p) => p.done);
      if (allDone && pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
        setIsRacing(false);
      }
    }, POLL_INTERVAL_MS);
  }

  return (
    <section id="race-mode">
      <div className="controls-row">
        <select value={difficulty} onChange={(e) => setDifficulty(e.target.value as Difficulty)}>
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>
        <span className="spacer" />
        <button type="button" className="primary" onClick={handleRace} disabled={isRacing}>
          {isRacing ? "Racing…" : "Race!"}
        </button>
      </div>
      <p className="race-hint">
        Every algorithm races through 100 {difficulty} puzzles live, each at its own pace — a
        struggling one is cut off after 30s.
      </p>

      {error && <p className="error">{error}</p>}

      {progress && (
        <div className="race-grid">
          {algorithms.map((algorithm) => (
            <RacePanel
              key={algorithm}
              algorithm={algorithm}
              progress={progress[algorithm]}
              puzzleCount={puzzleCount}
            />
          ))}
        </div>
      )}
    </section>
  );
}
