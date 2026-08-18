import type { PlaybackAction, PlaybackState } from "../playback/reducer";
import "./PlaybackControls.css";

const SPEED_OPTIONS = [1, 2, 5, 10, 20, 40];

interface PlaybackControlsProps {
  state: PlaybackState;
  dispatch: (action: PlaybackAction) => void;
}

export function PlaybackControls({ state, dispatch }: PlaybackControlsProps) {
  const atStart = state.stepIndex === 0;
  const atEnd = state.stepIndex >= state.totalSteps;

  return (
    <div className="playback-controls">
      <div className="playback-buttons">
        <button
          type="button"
          onClick={() => dispatch({ type: "stepBackward" })}
          disabled={atStart}
          aria-label="Step back"
        >
          ◀
        </button>
        <button
          type="button"
          className="play-toggle"
          onClick={() => dispatch({ type: "toggle" })}
          disabled={atEnd && !state.isPlaying}
        >
          {state.isPlaying ? "Pause" : "Play"}
        </button>
        <button
          type="button"
          onClick={() => dispatch({ type: "stepForward" })}
          disabled={atEnd}
          aria-label="Step forward"
        >
          ▶
        </button>
      </div>

      <input
        type="range"
        className="scrubber"
        min={0}
        max={state.totalSteps}
        value={state.stepIndex}
        onChange={(e) => dispatch({ type: "scrub", index: Number(e.target.value) })}
        aria-label="Scrub through solve steps"
      />

      <div className="playback-meta">
        <span>
          Step {state.stepIndex} / {state.totalSteps}
        </span>
        <label>
          Speed
          <select
            value={state.speedStepsPerSecond}
            onChange={(e) => dispatch({ type: "setSpeed", speed: Number(e.target.value) })}
          >
            {SPEED_OPTIONS.map((speed) => (
              <option key={speed} value={speed}>
                {speed}/s
              </option>
            ))}
          </select>
        </label>
      </div>
    </div>
  );
}
