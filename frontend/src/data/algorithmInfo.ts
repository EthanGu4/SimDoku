import type { MiniGridVariant } from "../components/MiniGrid";

export interface AlgorithmInfo {
  title: string;
  summary: string;
  pros: string[];
  cons: string[];
  history: string;
  animation: MiniGridVariant;
}

/** Keyed by the backend's solver registry name (see `app/solvers/*.py`).
 * An algorithm with no entry here just won't get a tab — this is
 * supplementary content, not part of the solve contract, so a new solver
 * still works without anyone touching this file. */
export const ALGORITHM_INFO: Record<string, AlgorithmInfo> = {
  backtracking: {
    title: "Backtracking",
    animation: "backtracking",
    summary:
      "Picks the most-constrained empty cell, tries each legal digit in turn, and recurses. When a branch leads to a dead end, it undoes the last placement and tries the next candidate.",
    pros: [
      "Guaranteed to find a solution if one exists",
      "Simple to implement and reason about",
      "Works on any valid puzzle with no tuning",
    ],
    cons: [
      "Can blow up exponentially on adversarial puzzles",
      "Speed depends heavily on cell-ordering heuristics",
      "Doesn't mimic how a human actually solves",
    ],
    history:
      "Backtracking search dates to the 1950s–60s, formalized by Golomb & Baumert in 1965 — it's the default exhaustive strategy behind most constraint-satisfaction solvers.",
  },
  constraint_propagation: {
    title: "Constraint Propagation",
    animation: "constraint-propagation",
    summary:
      "Applies pure logical deduction first — if a cell has only one possible value left (a naked single), or a digit can only go in one spot in a row/column/box (a hidden single), place it — before falling back to backtracking once deduction stalls.",
    pros: [
      "Mirrors how human solvers actually work",
      "Often much faster — deduction prunes the search early",
      "Produces a trace that's easy to narrate",
    ],
    cons: [
      "Naked/hidden singles alone can't solve every puzzle",
      "More code complexity than plain backtracking",
      "Still needs a backtracking fallback for hard puzzles",
    ],
    history:
      "These are exactly the techniques in human \"how to solve Sudoku\" guides. As a general AI technique, constraint propagation traces back to 1970s CSP research, like Waltz's arc-consistency work on scene labeling.",
  },
  dancing_links: {
    title: "Dancing Links (Algorithm X)",
    animation: "dancing-links",
    summary:
      "Reframes Sudoku as an exact-cover problem — 729 candidate placements against 324 constraints — and searches it with Knuth's Algorithm X, using a circular doubly-linked list (\"dancing links\") so undoing a choice is as cheap as making one.",
    pros: [
      "Very fast in practice — often the fastest here",
      "Backtracking is O(1) thanks to the linked-list trick",
      "Generalizes to any exact-cover puzzle unchanged",
    ],
    cons: [
      "Much harder to understand and implement",
      "Steps are constraint-column choices, not intuitive digit placements",
      "Doesn't produce human-readable reasoning",
    ],
    history:
      "Introduced by Donald Knuth in his 2000 paper \"Dancing Links\" as an elegant, general algorithm for exact-cover problems — Sudoku is one of its most common demonstrations today.",
  },
  simulated_annealing: {
    title: "Simulated Annealing",
    animation: "simulated-annealing",
    summary:
      "Starts from a random, box-valid guess, then repeatedly swaps two cells within a box and measures whether it reduces row/column conflicts. Even worsening moves are sometimes accepted — with shrinking probability as the \"temperature\" cools — to escape local optima.",
    pros: [
      "General-purpose — works on many problems beyond Sudoku",
      "Needs no domain-specific solving rules",
      "Visualizes search as settling rather than deducing",
    ],
    cons: [
      "Not complete — can get stuck and fail to converge",
      "Sensitive to its cooling schedule and parameters",
      "Usually slower and less reliable here than the other three",
    ],
    history:
      "Introduced by Kirkpatrick, Gelatt & Vecchi in 1983, inspired by annealing metal — heating it, then cooling slowly so it settles into a low-energy crystalline state.",
  },
  neural_net: {
    title: "Neural Net",
    animation: "neural-net",
    summary:
      "A small CNN trained on synthetic puzzles predicts a probability distribution over digits 1-9 for every empty cell. Each round, it places whichever (cell, digit) it's most confident about — checked against Sudoku's rules first — and repeats on the updated board.",
    pros: [
      "No hand-written solving rules — the strategy is entirely learned",
      "Every placement it makes is still rule-checked, so it never corrupts the board",
      "Fast per step — one small forward pass, no search tree",
    ],
    cons: [
      "No backtracking — a confident-but-wrong early guess can dead-end it",
      "Not complete, like simulated annealing — can get stuck and stop early",
      "Only as good as its (small, synthetic) training data",
    ],
    history:
      "Convolutional neural nets for Sudoku are a popular deep-learning demo project — a good illustration that a model with zero hard-coded rules can still learn a lot of Sudoku's structure purely from solved examples.",
  },
};
