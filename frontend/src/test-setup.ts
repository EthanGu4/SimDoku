import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";
import "@testing-library/jest-dom/vitest";

// @testing-library/react's auto-cleanup relies on a global `afterEach`,
// which Vitest only provides when `test.globals: true` is set. We don't set
// that (tests explicitly import from "vitest" instead), so wire it up here.
afterEach(cleanup);
