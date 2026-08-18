import type { paths } from "../api/schema";

type GeneratedResult =
  paths["/solve/{algorithm}"]["post"]["responses"][200]["content"]["application/json"];

// openapi-fetch's response typing (its `Readable<T>` helper) collapses fixed-length
// tuples to plain arrays at the client boundary, so `cell` never actually arrives
// typed as `[number, number]` — normalize it here to match what's really returned.
export type SolveStep = Omit<GeneratedResult["steps"][number], "cell"> & { cell: number[] };
export type SolveResult = Omit<GeneratedResult, "steps"> & { steps: SolveStep[] };
export type SolveStats = GeneratedResult["stats"];
export type BoardCells = number[][];
