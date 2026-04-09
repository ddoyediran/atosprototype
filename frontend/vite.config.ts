import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // @ maps to src/ — use @/features/... instead of ../../features/...
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    // Proxy API calls to the FastAPI backend in development.
    // Change target to your deployed backend URL via VITE_API_BASE in .env.production
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        // Needed for SSE: disable proxy-level buffering so chunks
        // are forwarded to the browser as they arrive.
        configure(proxy) {
          // Return a clear JSON error when the backend is unreachable
          // so the frontend shows a helpful message instead of an opaque 500.
          proxy.on('error', (_err, _req, res) => {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const r = res as any
            if (!r.headersSent) {
              r.writeHead(503, { 'Content-Type': 'application/json' })
              r.end(JSON.stringify({ detail: 'Backend unavailable — is uvicorn running on port 8000?' }))
            }
          })
        },
      },
    },
  },
  build: {
    // Produce source maps for error tracking in production (Sentry, etc.)
    sourcemap: true,
    // Raise the chunk size warning threshold slightly — the app is intentionally
    // kept slim, but SSE + Zustand + Zod together are ~50kB gzipped.
    chunkSizeWarningLimit: 600,
  },
})