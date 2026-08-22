import { useEffect, useState } from "react";
import { api } from "../api/client";
import { ALGORITHM_INFO } from "../data/algorithmInfo";
import "./AlgorithmInfoPanel.css";
import { MiniGrid } from "./MiniGrid";

interface AlgorithmInfoPanelProps {
  onClose: () => void;
}

// Tab order always follows this file's declaration order, never whatever
// order the backend happens to return — the registry list is only ever
// used below to drop a tab for something that isn't actually registered,
// never to reorder. Otherwise the tabs visibly reshuffle the moment that
// fetch resolves (it returns algorithms alphabetically).
const ORDERED_ALGORITHMS = Object.keys(ALGORITHM_INFO);

/** Self-sufficient: fetches its own algorithm list, so it can be triggered
 * from anywhere in the app (the header menu) without any page needing to
 * hand it state. */
export function AlgorithmInfoPanel({ onClose }: AlgorithmInfoPanelProps) {
  const [registeredAlgorithms, setRegisteredAlgorithms] = useState<string[] | null>(null);
  const [activeTab, setActiveTab] = useState(ORDERED_ALGORITHMS[0] ?? "");

  useEffect(() => {
    api.GET("/solve/algorithms").then(({ data }) => {
      if (data) setRegisteredAlgorithms(data);
    });
  }, []);

  const knownAlgorithms = registeredAlgorithms
    ? ORDERED_ALGORITHMS.filter((name) => registeredAlgorithms.includes(name))
    : ORDERED_ALGORITHMS;

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
