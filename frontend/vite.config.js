import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/calculate': 'http://localhost:8000',
      '/collision-vs-year': 'http://localhost:8000',
      '/monte-carlo': 'http://localhost:8000',
      '/petri-net': 'http://localhost:8000',
    }
  }
})
