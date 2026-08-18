import { useState } from "react";
import "./App.css";
import { RaceMode } from "./components/RaceMode";
import { SolvePage } from "./components/SolvePage";

type View = "solve" | "race";

function App() {
  const [view, setView] = useState<View>("solve");

  return (
    <>
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
    </>
  );
}

export default App;
