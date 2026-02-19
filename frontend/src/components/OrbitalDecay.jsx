import { useState } from 'react'
import { motion } from 'framer-motion'

const API_BASE = ''

const cardStyle = {
  background: 'var(--bg-card)',
  borderRadius: '12px',
  padding: '1.5rem',
  border: '1px solid var(--border)',
}

export default function OrbitalDecay() {
  const [form, setForm] = useState({
    initial_altitude_km: 400,
    cross_sectional_area_m2: 10,
    mass_kg: 1000,
    decay_altitude_km: 200,
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((f) => ({ ...f, [name]: parseFloat(value) || 0 }))
  }

  const handlePredict = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/predict-decay`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      const data = await res.json()
      setResult(data)
    } catch (e) {
      setResult({ error: e.message })
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      style={cardStyle}
    >
      <h3 style={{ marginBottom: '1rem', fontSize: '1.1rem', color: 'var(--accent)' }}>
        Atmospheric Drag Decay Prediction
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '0.75rem' }}>
        <div>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Initial Altitude (km)</label>
          <input
            type="number"
            name="initial_altitude_km"
            value={form.initial_altitude_km}
            onChange={handleChange}
            style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-dark)', color: 'var(--text)' }}
          />
        </div>
        <div>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Cross-Sectional Area (m²)</label>
          <input
            type="number"
            name="cross_sectional_area_m2"
            value={form.cross_sectional_area_m2}
            onChange={handleChange}
            style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-dark)', color: 'var(--text)' }}
          />
        </div>
        <div>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Mass (kg)</label>
          <input
            type="number"
            name="mass_kg"
            value={form.mass_kg}
            onChange={handleChange}
            style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-dark)', color: 'var(--text)' }}
          />
        </div>
        <div>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Decay Altitude (km)</label>
          <input
            type="number"
            name="decay_altitude_km"
            value={form.decay_altitude_km}
            onChange={handleChange}
            style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-dark)', color: 'var(--text)' }}
          />
        </div>
      </div>
      <button
        onClick={handlePredict}
        disabled={loading}
        style={{
          marginTop: '1rem',
          padding: '0.5rem 1rem',
          borderRadius: '6px',
          border: 'none',
          background: 'var(--accent)',
          color: 'var(--bg-dark)',
          fontWeight: 600,
          cursor: loading ? 'not-allowed' : 'pointer',
        }}
      >
        {loading ? 'Predicting...' : 'Predict Lifetime'}
      </button>
      {result && !result.error && (
        <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(0,212,170,0.1)', borderRadius: '8px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: '0.75rem', fontFamily: 'JetBrains Mono' }}>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Lifetime</div>
              <div style={{ color: 'var(--accent)', fontWeight: 700 }}>
                {result.lifetime_days.toFixed(0)} days
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                ({(result.lifetime_days / 365).toFixed(1)} years)
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Decay Rate</div>
              <div style={{ color: 'var(--accent)' }}>
                {result.decay_rate_km_day.toFixed(4)} km/day
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Final Altitude</div>
              <div style={{ color: 'var(--accent)' }}>
                {result.final_altitude_km.toFixed(2)} km
              </div>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  )
}
