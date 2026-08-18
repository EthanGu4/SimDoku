import { describe, expect, it } from "vitest";
import { initPlaybackState, playbackReducer } from "./reducer";

describe("playbackReducer", () => {
  it("starts paused at step 0", () => {
    const state = initPlaybackState(10);
    expect(state).toEqual({
      stepIndex: 0,
      totalSteps: 10,
      isPlaying: false,
      speedStepsPerSecond: 5,
    });
  });

  it("play sets isPlaying, but not when already at the end", () => {
    const atStart = playbackReducer(initPlaybackState(3), { type: "play" });
    expect(atStart.isPlaying).toBe(true);

    const atEnd = playbackReducer({ ...initPlaybackState(3), stepIndex: 3 }, { type: "play" });
    expect(atEnd.isPlaying).toBe(false);
  });

  it("toggle flips play state, respecting the end-of-trace guard", () => {
    const playing = playbackReducer(initPlaybackState(3), { type: "toggle" });
    expect(playing.isPlaying).toBe(true);

    const pausedAgain = playbackReducer(playing, { type: "toggle" });
    expect(pausedAgain.isPlaying).toBe(false);

    const stuckAtEnd = playbackReducer({ ...initPlaybackState(3), stepIndex: 3 }, { type: "toggle" });
    expect(stuckAtEnd.isPlaying).toBe(false);
  });

  it("tick advances by one step and stops at the end", () => {
    let state = initPlaybackState(2);
    state = playbackReducer(state, { type: "tick" });
    expect(state.stepIndex).toBe(1);
    expect(state.isPlaying).toBe(false);

    state = playbackReducer({ ...state, isPlaying: true }, { type: "tick" });
    expect(state.stepIndex).toBe(2);
    expect(state.isPlaying).toBe(false); // reached the end, auto-pauses
  });

  it("stepForward/stepBackward clamp to [0, totalSteps] and pause", () => {
    const state = initPlaybackState(2);

    const backAtStart = playbackReducer(state, { type: "stepBackward" });
    expect(backAtStart.stepIndex).toBe(0);

    const forwardOnce = playbackReducer(state, { type: "stepForward" });
    expect(forwardOnce.stepIndex).toBe(1);

    const forwardPastEnd = playbackReducer(
      playbackReducer(forwardOnce, { type: "stepForward" }),
      { type: "stepForward" },
    );
    expect(forwardPastEnd.stepIndex).toBe(2);
    expect(forwardPastEnd.isPlaying).toBe(false);
  });

  it("scrub clamps out-of-range indices and pauses playback", () => {
    const playing = { ...initPlaybackState(10), isPlaying: true };

    expect(playbackReducer(playing, { type: "scrub", index: 4 })).toMatchObject({
      stepIndex: 4,
      isPlaying: false,
    });
    expect(playbackReducer(playing, { type: "scrub", index: -5 }).stepIndex).toBe(0);
    expect(playbackReducer(playing, { type: "scrub", index: 999 }).stepIndex).toBe(10);
  });

  it("setSpeed clamps to the allowed range", () => {
    const state = initPlaybackState(10);
    expect(playbackReducer(state, { type: "setSpeed", speed: 0 }).speedStepsPerSecond).toBe(1);
    expect(playbackReducer(state, { type: "setSpeed", speed: 1000 }).speedStepsPerSecond).toBe(60);
    expect(playbackReducer(state, { type: "setSpeed", speed: 12 }).speedStepsPerSecond).toBe(12);
  });

  it("reset returns to step 0, paused, keeping totalSteps", () => {
    const mid = { stepIndex: 7, totalSteps: 10, isPlaying: true, speedStepsPerSecond: 20 };
    expect(playbackReducer(mid, { type: "reset" })).toEqual(initPlaybackState(10));
  });

  it("handles a zero-step (degenerate) trace without erroring", () => {
    const state = initPlaybackState(0);
    expect(playbackReducer(state, { type: "play" }).isPlaying).toBe(false);
    expect(playbackReducer(state, { type: "stepForward" }).stepIndex).toBe(0);
  });
});
