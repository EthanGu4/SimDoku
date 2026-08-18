import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SolveVisualizer } from "./SolveVisualizer";
import type { BoardCells, SolveResult } from "../playback/types";

const INITIAL_CELLS: BoardCells = Array.from({ length: 9 }, () => Array(9).fill(0));

function makeResult(steps: number): SolveResult {
  return {
    solved: true,
    solved_board: { cells: INITIAL_CELLS },
    steps: Array.from({ length: steps }, (_, i) => ({
      action: "place" as const,
      cell: [0, i % 9],
      value: 1,
    })),
    stats: { algorithm: "backtracking", elapsed_time: 0.01, step_count: steps, given_count: 0 },
  };
}

describe("SolveVisualizer autoPlay", () => {
  it("stays paused by default", () => {
    render(<SolveVisualizer initialCells={INITIAL_CELLS} result={makeResult(5)} />);
    expect(screen.getByRole("button", { name: "Play" })).toBeInTheDocument();
  });

  it("starts playing immediately when autoPlay is set", () => {
    render(<SolveVisualizer initialCells={INITIAL_CELLS} result={makeResult(5)} autoPlay />);
    expect(screen.getByRole("button", { name: "Pause" })).toBeInTheDocument();
  });

  it("restarts from step 0 when a new result arrives with the same step count", () => {
    const first = makeResult(5);
    const { rerender } = render(
      <SolveVisualizer initialCells={INITIAL_CELLS} result={first} autoPlay />,
    );
    expect(screen.getByText(/step 0 \/ 5/i)).toBeInTheDocument();

    const second = makeResult(5); // same length, different object identity
    rerender(<SolveVisualizer initialCells={INITIAL_CELLS} result={second} autoPlay />);
    expect(screen.getByText(/step 0 \/ 5/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Pause" })).toBeInTheDocument();
  });
});
