import { useEffect, useState } from "react";
import "./App.css";
import { api } from "./api/client";
import { SolveVisualizer } from "./components/SolveVisualizer";
import type { BoardCells, SolveResult } from "./playback/types";

const SAMPLE_PUZZLE =
  "530070000600195000098000060800060003400803001700020006060000280000419005000080079";

function parsePuzzle(input: string): BoardCells | null {
  const trimmed = input.replace(/\s+/g, "");
  if (trimmed.length !== 81 || !/^[0-9.]+$/.test(trimmed)) return null;

  const cells: BoardCells = [];
  for (let row = 0; row < 9; row++) {
    const rowChars = trimmed.slice(row * 9, row * 9 + 9);
    cells.push([...rowChars].map((ch) => (ch === "." ? 0 : Number(ch))));
  }
  return cells;
}

function App() {
  const [puzzleText, setPuzzleText] = useState(SAMPLE_PUZZLE);
  const [algorithms, setAlgorithms] = useState<string[]>([]);
  const [algorithm, setAlgorithm] = useState("backtracking");
  const [result, setResult] = useState<SolveResult | null>(null);
  const [solvedFor, setSolvedFor] = useState<BoardCells | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSolving, setIsSolving] = useState(false);

  useEffect(() => {
    api.GET("/solve/algorithms").then(({ data }) => {
      if (data && data.length > 0) {
        setAlgorithms(data);
        setAlgorithm(data[0]);
      }
    });
  }, []);

  async function handleSolve() {
    const cells = parsePuzzle(puzzleText);
    if (!cells) {
      setError("Enter exactly 81 characters (digits 1-9, and 0 or . for blank cells).");
      return;
    }

    setError(null);
    setIsSolving(true);
    const { data, error: apiError } = await api.POST("/solve/{algorithm}", {
      params: { path: { algorithm } },
      body: { cells },
    });
    setIsSolving(false);

    if (apiError) {
      setError("Couldn't solve that puzzle — check it doesn't violate Sudoku's rules.");
      return;
    }

    setResult(data);
    setSolvedFor(cells);
  }

  return (
    <>
      <header id="app-header">
        <h1>SimDoku</h1>
        <p>Watch Sudoku-solving algorithms run, one step at a time.</p>
      </header>

      <section id="puzzle-input">
        <label htmlFor="puzzle">Puzzle (81 chars, 0 or . for blank cells)</label>
        <textarea
          id="puzzle"
          value={puzzleText}
          onChange={(e) => setPuzzleText(e.target.value)}
          rows={3}
          spellCheck={false}
        />

        <div className="controls-row">
          <label htmlFor="algorithm">
            Algorithm
            <select
              id="algorithm"
              value={algorithm}
              onChange={(e) => setAlgorithm(e.target.value)}
            >
              {(algorithms.length > 0 ? algorithms : [algorithm]).map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </label>
          <button type="button" onClick={handleSolve} disabled={isSolving}>
            {isSolving ? "Solving…" : "Solve"}
          </button>
        </div>

        {error && <p className="error">{error}</p>}
      </section>

      {result && solvedFor && <SolveVisualizer initialCells={solvedFor} result={result} />}
    </>
  );
}

export default App;
