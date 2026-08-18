export interface PlaybackState {
  stepIndex: number;
  totalSteps: number;
  isPlaying: boolean;
  speedStepsPerSecond: number;
}

export type PlaybackAction =
  | { type: "play" }
  | { type: "pause" }
  | { type: "toggle" }
  | { type: "stepForward" }
  | { type: "stepBackward" }
  | { type: "scrub"; index: number }
  | { type: "setSpeed"; speed: number }
  | { type: "tick" }
  | { type: "reset" };

const MIN_SPEED = 1;
const MAX_SPEED = 60;
const DEFAULT_SPEED = 5;

export function initPlaybackState(totalSteps: number): PlaybackState {
  return {
    stepIndex: 0,
    totalSteps,
    isPlaying: false,
    speedStepsPerSecond: DEFAULT_SPEED,
  };
}

function clampIndex(index: number, totalSteps: number): number {
  return Math.max(0, Math.min(index, totalSteps));
}

function clampSpeed(speed: number): number {
  return Math.max(MIN_SPEED, Math.min(speed, MAX_SPEED));
}

export function playbackReducer(state: PlaybackState, action: PlaybackAction): PlaybackState {
  switch (action.type) {
    case "play":
      return state.stepIndex >= state.totalSteps ? state : { ...state, isPlaying: true };

    case "pause":
      return { ...state, isPlaying: false };

    case "toggle":
      if (state.isPlaying) return { ...state, isPlaying: false };
      return state.stepIndex >= state.totalSteps ? state : { ...state, isPlaying: true };

    case "stepForward":
      return {
        ...state,
        isPlaying: false,
        stepIndex: clampIndex(state.stepIndex + 1, state.totalSteps),
      };

    case "stepBackward":
      return {
        ...state,
        isPlaying: false,
        stepIndex: clampIndex(state.stepIndex - 1, state.totalSteps),
      };

    case "scrub":
      return { ...state, isPlaying: false, stepIndex: clampIndex(action.index, state.totalSteps) };

    case "setSpeed":
      return { ...state, speedStepsPerSecond: clampSpeed(action.speed) };

    case "tick": {
      const nextIndex = state.stepIndex + 1;
      if (nextIndex >= state.totalSteps) {
        return { ...state, stepIndex: state.totalSteps, isPlaying: false };
      }
      return { ...state, stepIndex: nextIndex };
    }

    case "reset":
      return initPlaybackState(state.totalSteps);

    default:
      return state;
  }
}
