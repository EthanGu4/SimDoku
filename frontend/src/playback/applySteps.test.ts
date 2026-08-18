import { describe, expect, it } from "vitest";
import { applySteps } from "./applySteps";
import type { SolveStep } from "./types";

const EMPTY_ROW = [0, 0, 0];
const INITIAL = [EMPTY_ROW.slice(), EMPTY_ROW.slice(), EMPTY_ROW.slice()];

const STEPS: SolveStep[] = [
  { action: "place", cell: [0, 0], value: 5 },
  { action: "place", cell: [1, 1], value: 7 },
  { action: "remove", cell: [0, 0], value: 5 },
  { action: "place", cell: [0, 0], value: 9 },
];

describe("applySteps", () => {
  it("returns the initial board unchanged for count 0", () => {
    expect(applySteps(INITIAL, STEPS, 0)).toEqual(INITIAL);
  });

  it("applies place and remove diffs incrementally", () => {
    expect(applySteps(INITIAL, STEPS, 1)[0][0]).toBe(5);
    expect(applySteps(INITIAL, STEPS, 2)[1][1]).toBe(7);
    expect(applySteps(INITIAL, STEPS, 3)[0][0]).toBe(0);
    expect(applySteps(INITIAL, STEPS, 4)[0][0]).toBe(9);
  });

  it("does not mutate the initial board it was given", () => {
    const before = INITIAL.map((row) => [...row]);
    applySteps(INITIAL, STEPS, 4);
    expect(INITIAL).toEqual(before);
  });

  it("tolerates a degenerate zero-step trace", () => {
    expect(applySteps(INITIAL, [], 0)).toEqual(INITIAL);
  });

  it("clamps count beyond the trace length", () => {
    expect(applySteps(INITIAL, STEPS, 999)).toEqual(applySteps(INITIAL, STEPS, STEPS.length));
  });
});
