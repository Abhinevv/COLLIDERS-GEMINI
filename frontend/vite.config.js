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
      '/celestrak': 'http://localhost:8000',
      '/calculate-from-celestrak': 'http://localhost:8000',
      '/calculate-enhanced': 'http://localhost:8000',
      '/simulate-breakup': 'http://localhost:8000',
      '/predict-decay': 'http://localhost:8000',
      '/propagate-orbit': 'http://localhost:8000',
    }
  }
})
