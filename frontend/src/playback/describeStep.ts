import type { SolveStep } from "./types";

export type StepKind = "positive" | "rejected" | "negative" | null;

/** How a step's cell should be highlighted: green for an accepted
 * placement, amber for an instantly-rejected trial, red for anything being
 * removed (backtrack or undoing a reject). */
export function stepKind(step: SolveStep | null): StepKind {
  if (!step) return null;
  if (step.action === "place") {
    return step.reasoning === "reject" ? "rejected" : "positive";
  }
  return "negative";
}

function formatCell(cell: number[]): string {
  const [row, col] = cell;
  return `row ${row + 1}, col ${col + 1}`;
}

/** A human-readable narration of what a solver just did, so watching the
 * playback actually explains the algorithm instead of just animating
 * numbers appearing. */
export function describeStep(step: SolveStep | null): string {
  if (!step) return "Press play or step forward to begin.";

  const pos = formatCell(step.cell);

  if (step.action === "place") {
    switch (step.reasoning) {
      case "reject":
        return `Trying ${step.value} at ${pos} — conflicts with a peer, rejected`;
      case "search":
        return `Trying ${step.value} at ${pos} — valid so far, continuing`;
      case "naked single":
        return `Placing ${step.value} at ${pos} — only candidate left (naked single)`;
      case "anneal":
        return `Swapping ${step.value} into ${pos}`;
      case "random init":
        return `Randomly filling ${pos} with ${step.value}`;
      default:
        if (step.reasoning?.startsWith("hidden single")) {
          return `Placing ${step.value} at ${pos} — ${step.reasoning}`;
        }
        return `Placing ${step.value} at ${pos}`;
    }
  }

  if (step.reasoning === "backtrack") {
    return `Dead end — removing ${step.value} from ${pos}, backtracking`;
  }
  return `Undoing ${step.value} at ${pos}`;
}
