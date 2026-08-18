import { describe, expect, it } from "vitest";
import { describeStep, stepKind } from "./describeStep";
import type { SolveStep } from "./types";

describe("stepKind", () => {
  it("is null when there is no step", () => {
    expect(stepKind(null)).toBeNull();
  });

  it("is positive for an accepted placement", () => {
    const step: SolveStep = { action: "place", cell: [0, 0], value: 5, reasoning: "search" };
    expect(stepKind(step)).toBe("positive");
  });

  it("is positive for a placement with no reasoning at all", () => {
    const step: SolveStep = { action: "place", cell: [0, 0], value: 5 };
    expect(stepKind(step)).toBe("positive");
  });

  it("is rejected for an instantly-rejected trial", () => {
    const step: SolveStep = { action: "place", cell: [0, 0], value: 5, reasoning: "reject" };
    expect(stepKind(step)).toBe("rejected");
  });

  it("is negative for any removal", () => {
    const backtrack: SolveStep = { action: "remove", cell: [0, 0], value: 5, reasoning: "backtrack" };
    const undoReject: SolveStep = { action: "remove", cell: [0, 0], value: 5 };
    expect(stepKind(backtrack)).toBe("negative");
    expect(stepKind(undoReject)).toBe("negative");
  });
});

describe("describeStep", () => {
  it("has a fallback message when there is no step", () => {
    expect(describeStep(null)).toMatch(/press play|step forward/i);
  });

  it.each([
    ["reject", /conflicts/i],
    ["search", /valid so far/i],
    ["naked single", /naked single/i],
    ["hidden single in row", /hidden single in row/i],
    ["anneal", /swapping/i],
    ["random init", /randomly filling/i],
  ])("describes a place step with reasoning %s", (reasoning, expected) => {
    const step: SolveStep = { action: "place", cell: [2, 4], value: 7, reasoning };
    expect(describeStep(step)).toMatch(expected);
    expect(describeStep(step)).toContain("row 3, col 5");
  });

  it("describes a backtrack removal distinctly from a plain undo", () => {
    const backtrack: SolveStep = {
      action: "remove",
      cell: [0, 0],
      value: 3,
      reasoning: "backtrack",
    };
    const undo: SolveStep = { action: "remove", cell: [0, 0], value: 3 };
    expect(describeStep(backtrack)).toMatch(/dead end/i);
    expect(describeStep(undo)).not.toMatch(/dead end/i);
  });
});
