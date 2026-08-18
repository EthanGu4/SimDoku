import { stepKind } from "../playback/describeStep";
import type { BoardCells, SolveStep } from "../playback/types";
import "./Board.css";

interface BoardProps {
  cells: BoardCells;
  givenCells: BoardCells;
  lastStep?: SolveStep | null;
}

export function Board({ cells, givenCells, lastStep }: BoardProps) {
  const activeCell = lastStep?.cell ?? null;
  const activeKind = stepKind(lastStep ?? null);

  return (
    <div className="sudoku-board" role="grid" aria-label="Sudoku board">
      {cells.map((row, rowIndex) =>
        row.map((value, colIndex) => {
          const isGiven = givenCells[rowIndex][colIndex] !== 0;
          const isActive = activeCell?.[0] === rowIndex && activeCell?.[1] === colIndex;

          const classes = [
            "cell",
            value === 0 ? "empty" : isGiven ? "given" : "solved",
            isActive && activeKind ? `active-${activeKind}` : "",
            colIndex % 3 === 2 && colIndex !== 8 ? "border-right-thick" : "",
            rowIndex % 3 === 2 && rowIndex !== 8 ? "border-bottom-thick" : "",
          ]
            .filter(Boolean)
            .join(" ");

          return (
            <div
              key={`${rowIndex}-${colIndex}`}
              role="gridcell"
              aria-label={value !== 0 ? `Row ${rowIndex + 1}, column ${colIndex + 1}: ${value}` : `Row ${rowIndex + 1}, column ${colIndex + 1}: empty`}
              className={classes}
            >
              {value !== 0 ? value : ""}
            </div>
          );
        }),
      )}
    </div>
  );
}
