import { useRef } from "react";
import type { BoardCells } from "../playback/types";
import "./PuzzleGridInput.css";

interface PuzzleGridInputProps {
  cells: BoardCells;
  onChange: (cells: BoardCells) => void;
}

function parseFullPuzzleString(text: string): BoardCells | null {
  const trimmed = text.replace(/\s+/g, "");
  if (trimmed.length !== 81 || !/^[0-9.]+$/.test(trimmed)) return null;

  const cells: BoardCells = [];
  for (let row = 0; row < 9; row++) {
    const rowChars = trimmed.slice(row * 9, row * 9 + 9);
    cells.push([...rowChars].map((ch) => (ch === "." ? 0 : Number(ch))));
  }
  return cells;
}

/** A clickable/typeable 9x9 grid for entering a puzzle by hand — pasting a
 * full 81-character puzzle string into any cell also works. */
export function PuzzleGridInput({ cells, onChange }: PuzzleGridInputProps) {
  const inputRefs = useRef<(HTMLInputElement | null)[][]>(
    Array.from({ length: 9 }, () => Array(9).fill(null)),
  );

  function setCell(row: number, col: number, value: number) {
    const next = cells.map((r) => [...r]);
    next[row][col] = value;
    onChange(next);
  }

  function focusCell(row: number, col: number) {
    if (row < 0 || row > 8 || col < 0 || col > 8) return;
    inputRefs.current[row]?.[col]?.focus();
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>, row: number, col: number) {
    if (e.key >= "1" && e.key <= "9") {
      e.preventDefault();
      setCell(row, col, Number(e.key));
      focusCell(col + 1 > 8 ? row + 1 : row, col + 1 > 8 ? 0 : col + 1);
    } else if (e.key === "0") {
      // Treated like a digit (advances focus) so a blank puzzle can be
      // typed out cell-by-cell, not just pasted as a whole string.
      e.preventDefault();
      setCell(row, col, 0);
      focusCell(col + 1 > 8 ? row + 1 : row, col + 1 > 8 ? 0 : col + 1);
    } else if (e.key === "Backspace" || e.key === "Delete") {
      // Corrects the current cell in place — deliberately doesn't advance.
      e.preventDefault();
      setCell(row, col, 0);
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      focusCell(row, col + 1);
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      focusCell(row, col - 1);
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      focusCell(row + 1, col);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      focusCell(row - 1, col);
    }
  }

  function handlePaste(e: React.ClipboardEvent) {
    const parsed = parseFullPuzzleString(e.clipboardData.getData("text"));
    if (parsed) {
      e.preventDefault();
      onChange(parsed);
    }
  }

  return (
    <div
      className="puzzle-grid-input"
      role="grid"
      aria-label="Sudoku puzzle input"
      onPaste={handlePaste}
    >
      {cells.map((row, rowIndex) =>
        row.map((value, colIndex) => (
          <input
            key={`${rowIndex}-${colIndex}`}
            ref={(el) => {
              inputRefs.current[rowIndex][colIndex] = el;
            }}
            className={[
              "puzzle-cell",
              colIndex % 3 === 2 && colIndex !== 8 ? "border-right-thick" : "",
              rowIndex % 3 === 2 && rowIndex !== 8 ? "border-bottom-thick" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            inputMode="numeric"
            maxLength={1}
            value={value === 0 ? "" : value}
            onKeyDown={(e) => handleKeyDown(e, rowIndex, colIndex)}
            onChange={(e) => {
              const digit = e.target.value.replace(/[^1-9]/g, "").slice(-1);
              setCell(rowIndex, colIndex, digit ? Number(digit) : 0);
            }}
            onFocus={(e) => e.target.select()}
            aria-label={`Row ${rowIndex + 1}, column ${colIndex + 1}`}
          />
        )),
      )}
    </div>
  );
}
