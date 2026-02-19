import { useState } from 'react'
import { motion } from 'framer-motion'

const API_BASE = ''

const cardStyle = {
  background: 'var(--bg-card)',
  borderRadius: '12px',
  padding: '1.5rem',
  border: '1px solid var(--border)',
}

export default function BreakupSimulation() {
  const [form, setForm] = useState({
    satellite_area_m2: 100,
    debris_diameter_mm: 10,
    relative_velocity_km_s: 10.0,
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((f) => ({ ...f, [name]: parseFloat(value) || 0 }))
  }

  const handleSimulate = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/simulate-breakup`, {
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
        Breakup Simulation (NASA SBM)
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '0.75rem' }}>
        <div>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Satellite Area (m²)</label>
          <input
            type="number"
            name="satellite_area_m2"
            value={form.satellite_area_m2}
            onChange={handleChange}
            style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-dark)', color: 'var(--text)' }}
          />
        </div>
        <div>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Debris Diameter (mm)</label>
          <input
            type="number"
            name="debris_diameter_mm"
            value={form.debris_diameter_mm}
            onChange={handleChange}
            style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-dark)', color: 'var(--text)' }}
          />
        </div>
        <div>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Relative Velocity (km/s)</label>
          <input
            type="number"
            name="relative_velocity_km_s"
            value={form.relative_velocity_km_s}
            onChange={handleChange}
            style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-dark)', color: 'var(--text)' }}
          />
        </div>
      </div>
      <button
        onClick={handleSimulate}
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
        {loading ? 'Simulating...' : 'Simulate Breakup'}
      </button>
      {result && !result.error && (
        <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(0,212,170,0.1)', borderRadius: '8px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: '0.75rem', marginBottom: '1rem' }}>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Collision Energy</div>
              <div style={{ color: 'var(--accent)', fontWeight: 700, fontFamily: 'JetBrains Mono' }}>
                {(result.collision_energy_joules / 1000).toFixed(2)} kJ
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Fragments</div>
              <div style={{ color: 'var(--accent)', fontWeight: 700 }}>{result.num_fragments}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Debris Mass</div>
              <div style={{ color: 'var(--accent)', fontFamily: 'JetBrains Mono' }}>
                {result.debris_mass_kg.toFixed(4)} kg
              </div>
            </div>
          </div>
          {result.fragments && result.fragments.length > 0 && (
            <div style={{ maxHeight: '200px', overflowY: 'auto', fontSize: '0.8rem', fontFamily: 'JetBrains Mono' }}>
              <div style={{ color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Sample Fragments:</div>
              {result.fragments.slice(0, 20).map((f, i) => (
                <div key={i} style={{ padding: '0.25rem', color: 'var(--text-muted)' }}>
                  #{i + 1}: {f.diameter_mm.toFixed(2)} mm, {f.mass_kg.toExponential(2)} kg
                </div>
              ))}
              {result.fragments.length > 20 && (
                <div style={{ color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                  ... and {result.fragments.length - 20} more fragments
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </motion.div>
  )
}
