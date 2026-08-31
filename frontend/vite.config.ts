import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Port 8000 was left occupied by a stuck orphaned listener on this dev
    // machine with no killable owning process (confirmed via netstat,
    // Get-NetTCPConnection, and Docker) — using 8010 as a workaround.
    proxy: { '/api': 'http://127.0.0.1:8010' },
  },
})
