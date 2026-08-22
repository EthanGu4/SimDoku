import { useState } from "react";
import "./App.css";
import { AlgorithmInfoPanel } from "./components/AlgorithmInfoPanel";
import { ComparePage } from "./components/ComparePage";
import { SolvePage } from "./components/SolvePage";

type View = "solve" | "compare";

function App() {
  const [view, setView] = useState<View>("solve");
  const [showAlgoInfo, setShowAlgoInfo] = useState(false);

  return (
    <>
      <button
        type="button"
        id="menu-button"
        onClick={() => setShowAlgoInfo(true)}
        aria-label="About the algorithms"
        title="About the algorithms"
      >
        ⋮
      </button>

      <header id="app-header">
        <h1>SimDoku</h1>
        <p>Watch Sudoku-solving algorithms run, one step at a time.</p>
        <nav id="view-tabs">
          <button
            type="button"
            className={view === "solve" ? "active" : ""}
            onClick={() => setView("solve")}
          >
            Solve
          </button>
          <button
            type="button"
            className={view === "compare" ? "active" : ""}
            onClick={() => setView("compare")}
          >
            Compare
          </button>
        </nav>
      </header>

      {view === "solve" ? <SolvePage /> : <ComparePage />}

      {showAlgoInfo && <AlgorithmInfoPanel onClose={() => setShowAlgoInfo(false)} />}
    </>
  );
}

export default App;
