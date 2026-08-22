import createClient from "openapi-fetch";
import type { paths } from "./schema";

// Same-origin by default: in production the backend serves this bundle, and
// in dev Vite proxies the API prefixes to :8000 (see vite.config.ts). Set
// VITE_API_BASE_URL only to point at a backend on a different origin.
export const api = createClient<paths>({
  baseUrl: import.meta.env.VITE_API_BASE_URL ?? "",
});

export type { components } from "./schema";
