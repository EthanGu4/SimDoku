import { useEffect, useState } from "react";
import { api } from "../api/client";
import { ALGORITHM_INFO } from "../data/algorithmInfo";
import "./AlgorithmInfoPanel.css";
import { MiniGrid } from "./MiniGrid";

interface AlgorithmInfoPanelProps {
  onClose: () => void;
}

/** Self-sufficient: fetches its own algorithm list, so it can be triggered
 * from anywhere in the app (the header menu) without any page needing to
 * hand it state. */
export function AlgorithmInfoPanel({ onClose }: AlgorithmInfoPanelProps) {
  const [knownAlgorithms, setKnownAlgorithms] = useState<string[]>(
    Object.keys(ALGORITHM_INFO),
  );
  const [activeTab, setActiveTab] = useState(knownAlgorithms[0] ?? "");

  useEffect(() => {
    api.GET("/solve/algorithms").then(({ data }) => {
      if (!data) return;
      const known = data.filter((name) => ALGORITHM_INFO[name]);
      if (known.length > 0) {
        setKnownAlgorithms(known);
        setActiveTab(known[0]);
      }
    });
  }, []);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const info = ALGORITHM_INFO[activeTab];

  return (
    <aside className="algo-panel" aria-label="About this algorithm">
      <div className="algo-panel-header">
        <h2>Algorithms</h2>
        <button type="button" className="algo-panel-close" onClick={onClose} aria-label="Close">
          ×
        </button>
      </div>

      <div className="algo-panel-tabs" role="tablist">
        {knownAlgorithms.map((name) => (
          <button
            key={name}
            type="button"
            role="tab"
            aria-selected={name === activeTab}
            className={name === activeTab ? "active" : ""}
            onClick={() => setActiveTab(name)}
          >
            {ALGORITHM_INFO[name].title}
          </button>
        ))}
      </div>

      {info && (
        <div className="algo-panel-body">
          <MiniGrid variant={info.animation} />

          <p className="algo-summary">{info.summary}</p>

          <h3>Pros</h3>
          <ul className="algo-pros">
            {info.pros.map((pro) => (
              <li key={pro}>{pro}</li>
            ))}
          </ul>

          <h3>Cons</h3>
          <ul className="algo-cons">
            {info.cons.map((con) => (
              <li key={con}>{con}</li>
            ))}
          </ul>

          <h3>History</h3>
          <p className="algo-history">{info.history}</p>
        </div>
      )}
    </aside>
  );
}
