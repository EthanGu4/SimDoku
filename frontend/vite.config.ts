/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// The API is called with same-origin relative URLs so one built bundle works
// whether it's served by the backend (as in the Docker image) or by this dev
// server. In dev these prefixes are proxied to the backend on :8000, which
// also means no CORS is involved in either mode.
const API_PREFIXES = ['/solve', '/puzzles', '/board', '/health']

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: Object.fromEntries(
      API_PREFIXES.map((prefix) => [prefix, { target: 'http://localhost:8000' }]),
    ),
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts'],
  },
})
