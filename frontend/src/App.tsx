import { useState } from "react";
import "./App.css";
import { AlgorithmInfoPanel } from "./components/AlgorithmInfoPanel";
import { RaceMode } from "./components/RaceMode";
import { SolvePage } from "./components/SolvePage";

type View = "solve" | "race";

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
            className={view === "race" ? "active" : ""}
            onClick={() => setView("race")}
          >
            Race
          </button>
        </nav>
      </header>

      {view === "solve" ? <SolvePage /> : <RaceMode />}

      {showAlgoInfo && <AlgorithmInfoPanel onClose={() => setShowAlgoInfo(false)} />}
    </>
  );
}

export default App;
