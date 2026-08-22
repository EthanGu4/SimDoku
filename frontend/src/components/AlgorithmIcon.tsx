/** Small stroke-based icons, one per registered algorithm, used in the race
 * overview strip and panel headers. Deliberately plain (currentColor,
 * no fills/gradients) to match the app's existing visual language — these
 * are identity markers, not illustrations. Falls back to a plain dot for
 * any algorithm without a dedicated icon, so a new solver never breaks
 * this purely-decorative piece. */

interface AlgorithmIconProps {
  algorithm: string;
  size?: number;
}

const ICON_PATHS: Record<string, React.ReactNode> = {
  backtracking: (
    <path d="M14 5a5 5 0 1 1-3.5 8.5M5 5v5h5M5 10 3 8m2 2 2-2" />
  ),
  constraint_propagation: (
    <path d="M10 3a5 5 0 0 1 3 9c-.6.5-1 1.2-1 2H8c0-.8-.4-1.5-1-2a5 5 0 0 1 3-9ZM8 17h4M9 15h2" />
  ),
  dancing_links: (
    <path d="M7 6a3 3 0 0 0 0 6h1M13 8a3 3 0 0 1 0 6h-1M8 9h4" />
  ),
  simulated_annealing: (
    <path d="M10 2c1.5 3-1.5 4-1.5 6.5A2.5 2.5 0 0 0 11 11a3.5 3.5 0 0 0 3-5.5C15.5 8 16 10.5 14.5 13a4.5 4.5 0 0 1-9 0C5.5 9.5 8.5 8 10 2Z" />
  ),
  neural_net: (
    <path d="M4 6a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3ZM4 17a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3ZM16 10a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3ZM4 6v8M4 6l12 2.5M4 14l12-2.5" />
  ),
  algorithm_picker: <path d="M10 2v3M10 15v3M2 10h3M15 10h3M10 6a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z" />,
  genetic: (
    <path d="M6 3c0 4 8 4 8 7s-8 3-8 7M14 3c0 4-8 4-8 7s8 3 8 7M7 6h6M7 14h6" />
  ),
  // The four corners an X-Wing keys off, plus the lines linking them.
  x_wing_swordfish: (
    <path d="M6 6h.01M14 6h.01M6 14h.01M14 14h.01M6 6h8M6 14h8M6 6v8M14 6v8M6 6l8 8M14 6l-8 8" />
  ),
};

export function AlgorithmIcon({ algorithm, size = 18 }: AlgorithmIconProps) {
  const path = ICON_PATHS[algorithm];
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.4"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {path ?? <circle cx="10" cy="10" r="3" />}
    </svg>
  );
}
