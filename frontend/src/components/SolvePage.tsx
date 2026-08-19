import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { BoardCells, SolveResult } from "../playback/types";
import { CameraCapture } from "./CameraCapture";
import { PuzzleGridInput } from "./PuzzleGridInput";
import { SolveVisualizer } from "./SolveVisualizer";

const SAMPLE_PUZZLE_CELLS: BoardCells = [
  [5, 3, 0, 0, 7, 0, 0, 0, 0],
  [6, 0, 0, 1, 9, 5, 0, 0, 0],
  [0, 9, 8, 0, 0, 0, 0, 6, 0],
  [8, 0, 0, 0, 6, 0, 0, 0, 3],
  [4, 0, 0, 8, 0, 3, 0, 0, 1],
  [7, 0, 0, 0, 2, 0, 0, 0, 6],
  [0, 6, 0, 0, 0, 0, 2, 8, 0],
  [0, 0, 0, 4, 1, 9, 0, 0, 5],
  [0, 0, 0, 0, 8, 0, 0, 7, 9],
];

const EMPTY_CELLS: BoardCells = Array.from({ length: 9 }, () => Array(9).fill(0));

export function SolvePage() {
  const [puzzleCells, setPuzzleCells] = useState<BoardCells>(SAMPLE_PUZZLE_CELLS);
  const [algorithms, setAlgorithms] = useState<string[]>([]);
  const [algorithm, setAlgorithm] = useState("backtracking");
  const [result, setResult] = useState<SolveResult | null>(null);
  const [solvedFor, setSolvedFor] = useState<BoardCells | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSolving, setIsSolving] = useState(false);
  const [isDetecting, setIsDetecting] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.GET("/solve/algorithms").then(({ data }) => {
      if (data && data.length > 0) {
        setAlgorithms(data);
        setAlgorithm(data[0]);
      }
    });
  }, []);

  async function handleSolve() {
    setError(null);
    setIsSolving(true);
    const { data, error: apiError } = await api.POST("/solve/{algorithm}", {
      params: { path: { algorithm } },
      body: { cells: puzzleCells },
    });
    setIsSolving(false);

    if (apiError) {
      setError("Couldn't solve that puzzle — check it doesn't violate Sudoku's rules.");
      return;
    }

    setResult(data);
    setSolvedFor(puzzleCells);
  }

  function handleClear() {
    setPuzzleCells(EMPTY_CELLS);
    setResult(null);
    setSolvedFor(null);
    setError(null);
  }

  async function detectAndFillGrid(image: Blob) {
    setError(null);
    setIsDetecting(true);
    const formData = new FormData();
    formData.append("image", image);

    const { data, error: apiError } = await api.POST("/board/detect", {
      // openapi-fetch types this body as the multipart schema shape, but a
      // FormData instance is passed through to fetch() as-is (see its
      // defaultBodySerializer) — this cast just satisfies that mismatch.
      body: formData as never,
    });
    setIsDetecting(false);

    if (apiError) {
      setError("Couldn't read a puzzle grid from that photo — try a clearer, more square-on shot.");
      return;
    }

    setPuzzleCells(data.cells);
    setResult(null);
    setSolvedFor(null);
  }

  async function handlePhotoSelected(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (file) await detectAndFillGrid(file);
  }

  async function handlePhotoCaptured(blob: Blob) {
    setShowCamera(false);
    await detectAndFillGrid(blob);
  }

  return (
    <>
      <section id="puzzle-input">
        <PuzzleGridInput cells={puzzleCells} onChange={setPuzzleCells} />

        <div className="controls-row">
          <select value={algorithm} onChange={(e) => setAlgorithm(e.target.value)}>
            {(algorithms.length > 0 ? algorithms : [algorithm]).map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
          <span className="spacer" />
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            hidden
            onChange={handlePhotoSelected}
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isDetecting}
          >
            {isDetecting ? "Reading photo…" : "Upload photo"}
          </button>
          <button type="button" onClick={() => setShowCamera(true)} disabled={isDetecting}>
            Take photo
          </button>
          <button type="button" onClick={handleClear}>
            Clear
          </button>
          <button type="button" className="primary" onClick={handleSolve} disabled={isSolving}>
            {isSolving ? "Solving…" : "Solve"}
          </button>
        </div>

        {error && <p className="error">{error}</p>}
      </section>

      {result && solvedFor && <SolveVisualizer initialCells={solvedFor} result={result} />}

      {showCamera && (
        <CameraCapture onCapture={handlePhotoCaptured} onClose={() => setShowCamera(false)} />
      )}
    </>
  );
}
