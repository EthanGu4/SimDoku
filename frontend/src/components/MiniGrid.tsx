import "./MiniGrid.css";

export type MiniGridVariant =
  | "backtracking"
  | "constraint-propagation"
  | "dancing-links"
  | "simulated-annealing"
  | "neural-net"
  | "algorithm-picker"
  | "fish-patterns";

interface MiniGridProps {
  variant: MiniGridVariant;
}

/** A small looping CSS animation that gives a rough visual intuition for how
 * an algorithm behaves — not a real trace, just a decorative 3x3 grid whose
 * cells light up in a pattern specific to each variant (see MiniGrid.css). */
export function MiniGrid({ variant }: MiniGridProps) {
  return (
    <div className={`mini-grid mini-grid-${variant}`} aria-hidden="true">
      {Array.from({ length: 9 }, (_, i) => (
        <span key={i} className="mini-cell" style={{ "--i": i } as React.CSSProperties} />
      ))}
    </div>
  );
}
