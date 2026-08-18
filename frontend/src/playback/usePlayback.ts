import { useEffect, useReducer } from "react";
import { initPlaybackState, playbackReducer, type PlaybackAction } from "./reducer";

export function usePlayback(totalSteps: number) {
  const [state, dispatch] = useReducer(playbackReducer, totalSteps, initPlaybackState);

  useEffect(() => {
    dispatch({ type: "reset" });
    // totalSteps changing means a new SolveResult loaded — restart from the beginning.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [totalSteps]);

  useEffect(() => {
    if (!state.isPlaying) return;
    const intervalMs = 1000 / state.speedStepsPerSecond;
    const id = window.setInterval(() => dispatch({ type: "tick" }), intervalMs);
    return () => window.clearInterval(id);
  }, [state.isPlaying, state.speedStepsPerSecond]);

  return { state, dispatch: dispatch as (action: PlaybackAction) => void };
}
