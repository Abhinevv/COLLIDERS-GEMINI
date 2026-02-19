import { useState, useEffect, useMemo } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import { motion } from 'framer-motion'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const API_BASE = ''

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
  },
  scales: {
    x: {
      grid: { color: 'rgba(30,41,59,0.5)' },
      ticks: { color: '#94a3b8' },
    },
    y: {
      min: 0,
      max: 1,
      grid: { color: 'rgba(30,41,59,0.5)' },
      ticks: {
        color: '#94a3b8',
        callback: (v) => (v * 100).toFixed(0) + '%',
      },
    },
  },
}

export default function CollisionGraph({ payload }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!payload) return
    setLoading(true)
    fetch(`${API_BASE}/collision-vs-year`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then((r) => r.json())
      .then(setData)
      .finally(() => setLoading(false))
  }, [payload])

  const chartData = useMemo(() => {
    if (!data || !Array.isArray(data)) return null
    return {
      labels: data.map((d) => d.year),
      datasets: [
        {
          label: 'Collision Probability',
          data: data.map((d) => d.probability),
          borderColor: '#00d4aa',
          backgroundColor: 'rgba(0,212,170,0.15)',
          fill: true,
          tension: 0.3,
        },
      ],
    }
  }, [data])

  if (!payload) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      style={{
        background: 'var(--bg-card)',
        borderRadius: '12px',
        padding: '1.5rem',
        border: '1px solid var(--border)',
        height: '320px',
      }}
    >
      <h2 style={{ marginBottom: '1rem', fontSize: '1.25rem' }}>
        Collision Probability vs Year (2019–2030)
      </h2>
      {loading && <p style={{ color: 'var(--text-muted)' }}>Loading…</p>}
      {chartData && !loading && <Line data={chartData} options={chartOptions} />}
    </motion.div>
  )
}
