import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { BenchmarkPuzzle, BenchmarkRun, SolveResult } from "../playback/types";
import { SolveVisualizer } from "./SolveVisualizer";
import "./RaceMode.css";

type ResultsByAlgorithm = Record<string, SolveResult>;

export function RaceMode() {
  const [puzzles, setPuzzles] = useState<BenchmarkPuzzle[]>([]);
  const [algorithms, setAlgorithms] = useState<string[]>([]);
  const [puzzleId, setPuzzleId] = useState<string>("");
  const [results, setResults] = useState<ResultsByAlgorithm>({});
  const [history, setHistory] = useState<BenchmarkRun[]>([]);
  const [isRacing, setIsRacing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.GET("/puzzles").then(({ data }) => {
      if (data && data.length > 0) {
        setPuzzles(data);
        setPuzzleId(data[0].id);
      }
    });
    api.GET("/solve/algorithms").then(({ data }) => {
      if (data) setAlgorithms(data);
    });
  }, []);

  useEffect(() => {
    if (!puzzleId) return;
    api.GET("/benchmark/history", { params: { query: { puzzle_id: puzzleId } } }).then(
      ({ data }) => {
        if (data) setHistory(data);
      },
    );
  }, [puzzleId]);

  async function handleRace() {
    if (!puzzleId || algorithms.length === 0) return;
    setError(null);
    setIsRacing(true);
    setResults({});

    const responses = await Promise.all(
      algorithms.map((algorithm) =>
        api.POST("/benchmark/{algorithm}", {
          params: { path: { algorithm } },
          body: { puzzle_id: puzzleId },
        }),
      ),
    );

    setIsRacing(false);

    const next: ResultsByAlgorithm = {};
    let hadFailure = false;
    responses.forEach((response, i) => {
      if (response.data) {
        next[algorithms[i]] = response.data;
      } else {
        hadFailure = true;
      }
    });
    setResults(next);
    if (hadFailure) setError("One or more algorithms failed to run.");

    const { data: freshHistory } = await api.GET("/benchmark/history", {
      params: { query: { puzzle_id: puzzleId } },
    });
    if (freshHistory) setHistory(freshHistory);
  }

  const puzzle = puzzles.find((p) => p.id === puzzleId);
  const hasResults = Object.keys(results).length > 0;

  return (
    <section id="race-mode">
      <div className="controls-row">
        <select value={puzzleId} onChange={(e) => setPuzzleId(e.target.value)}>
          {puzzles.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name} — {p.given_count} givens
            </option>
          ))}
        </select>
        <span className="spacer" />
        <button
          type="button"
          className="primary"
          onClick={handleRace}
          disabled={isRacing || !puzzleId}
        >
          {isRacing ? "Racing…" : "Race!"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {hasResults && puzzle && (
        <div className="race-grid">
          {algorithms.map((algorithm) => {
            const result = results[algorithm];
            if (!result) return null;
            return (
              <div key={algorithm} className="race-panel">
                <h3>{algorithm}</h3>
                <SolveVisualizer initialCells={puzzle.board.cells} result={result} autoPlay />
              </div>
            );
          })}
        </div>
      )}

      {history.length > 0 && (
        <div id="benchmark-history">
          <h2>History</h2>
          <table>
            <thead>
              <tr>
                <th>Algorithm</th>
                <th>Solved</th>
                <th>Elapsed</th>
                <th>Steps</th>
                <th>When</th>
              </tr>
            </thead>
            <tbody>
              {history.map((run, i) => (
                <tr key={i}>
                  <td>{run.algorithm}</td>
                  <td>{run.solved ? "Yes" : "No"}</td>
                  <td>{(run.elapsed_time * 1000).toFixed(2)} ms</td>
                  <td>{run.step_count}</td>
                  <td>{new Date(run.created_at).toLocaleTimeString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
